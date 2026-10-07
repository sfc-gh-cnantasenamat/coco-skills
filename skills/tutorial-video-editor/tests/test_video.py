from pathlib import Path
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL/'scripts'))

import numpy as np
from compose import Composer, rounded_mask
from media import prepare_proxies
from project import canvas, ffmpeg, fingerprint, layout, load, preflight, probe, stream
from tutorial_video import render
from verify import verify


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.raw = json.loads((SKILL/'assets/project.example.json').read_text())
        self.path = self.root/'project.json'

    def tearDown(self):
        self.temp.cleanup()

    def config(self, raw=None):
        self.path.write_text(json.dumps(self.raw if raw is None else raw))
        return load(self.path)

    def test_default_resolution_and_path_resolution(self):
        self.raw.pop('proxy_height')
        config = self.config()
        self.assertEqual(config['proxy_height'], 720)
        self.assertEqual(canvas(720), (1280, 720))
        self.assertEqual(canvas(480), (854, 480))
        self.assertEqual(config['camera'], str((self.root/'camera.mp4').resolve()))

    def test_fullscreen_defaults_and_screen_corners(self):
        self.raw.pop('style')
        config = self.config()
        self.assertEqual(config['style']['screen_inset'], 0)
        self.assertEqual(config['style']['corner_radius'], 0)
        for height in (720, 1080, 1440, 2160):
            geometry = layout(config, height, 16/9)
            self.assertEqual(geometry['screen_left'], 0)
            self.assertEqual(geometry['screen_top'], 0)
            self.assertEqual(geometry['screen_width'], geometry['width'])
            self.assertEqual(geometry['screen_height'], height)
        geometry = layout(config, 720, 16/9)
        composer = Composer(config, geometry)
        np.testing.assert_array_equal(composer.screen_mask, np.ones((720, 1280)))
        camera = np.full((720, 1280, 3), 70, np.uint8)
        screen = np.full_like(camera, 230)
        result = composer.frame(camera, screen, config['tutorial_start'], 24)
        for row, column in ((0, 0), (0, -1), (-1, 0), (-1, -1)):
            np.testing.assert_array_equal(result[row, column], screen[row, column])

    def test_explicit_legacy_inset_and_480p(self):
        self.raw['proxy_height'] = 480
        self.raw['style'].update(screen_inset=16/720, corner_radius=12/720)
        config = self.config()
        self.assertEqual(config['proxy_height'], 480)
        self.assertEqual(config['style']['corner_radius'], 12/720)
        geometry = layout(config, 480, 16/9)
        self.assertGreater(geometry['screen_left'], 0)
        self.assertGreater(geometry['screen_top'], 0)

    def test_equal_margins_and_aspect_fit(self):
        config = self.config()
        for height in (480, 720, 2160):
            for ratio in (3686/2160, 16/9, 2.5, .75):
                geometry = layout(config, height, ratio)
                self.assertEqual(geometry['width']-geometry['presenter_left']-geometry['diameter'], geometry['margin'])
                self.assertEqual(height-geometry['presenter_top']-geometry['diameter'], geometry['margin'])
                self.assertLess(abs(geometry['screen_width']/geometry['screen_height']-ratio), .012)
                self.assertGreaterEqual(geometry['screen_left'], 0)
                self.assertGreaterEqual(geometry['screen_top'], 0)

    def test_invalid_configuration(self):
        for field, value in [('tutorial_start', 1), ('transition_frames', 1),
                             ('outro_start', 1440), ('revision', '../escape'),
                             ('proxy_height', 2160), ('camera_offset_seconds', -1), ('fps', '0')]:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.raw)
                changed[field] = value
                with self.assertRaises(ValueError):
                    self.config(changed)

    def test_unknown_setting(self):
        self.raw['proxy_heigth'] = 480
        with self.assertRaises(ValueError):
            self.config()

    def test_local_skill_structure(self):
        text = (SKILL/'SKILL.md').read_text()
        self.assertTrue(text.startswith('---\nname: tutorial-video-editor\n'))
        self.assertLess(len(text.splitlines()), 500)
        import re
        for relative in re.findall(r'\]\(([^)]+)\)', text):
            self.assertTrue((SKILL/relative).is_file(), relative)
        import tomllib
        dependencies = tomllib.loads((SKILL/'pyproject.toml').read_text())['project']['dependencies']
        self.assertEqual(len(dependencies), 3)

    def test_overflow(self):
        config = self.config()
        config['style']['presenter_diameter'] = 1
        with self.assertRaises(ValueError):
            layout(config, 480, 16/9)

    def test_circle_and_transition_endpoints(self):
        config = self.config()
        geometry = layout(config, 480, 16/9)
        composer = Composer(config, geometry)
        camera = np.full((480, 854, 3), 70, np.uint8)
        screen = np.full((geometry['screen_height'], geometry['screen_width'], 3), 230, np.uint8)
        self.assertEqual(rounded_mask(128, 128, 64)[0, 0], 0)
        start, outro, transition = config['tutorial_start'], config['outro_start'], config['transition_frames']
        np.testing.assert_array_equal(composer.frame(camera, screen, start-transition, 24), camera)
        np.testing.assert_array_equal(composer.frame(camera, screen, start-1, 24), composer.frame(camera, screen, start, 24))
        np.testing.assert_array_equal(composer.frame(camera, screen, outro, 24), composer.frame(camera, screen, outro-1, 24))
        np.testing.assert_array_equal(composer.frame(camera, screen, outro+transition-1, 24), camera)

    def test_rounded_square_and_transition_endpoints(self):
        self.raw['style'].update(presenter_corner_radius=.25, presenter_margin=.075,
                                 presenter_diameter=.28)
        config = self.config()
        geometry = layout(config, 720, 16/9)
        self.assertEqual(geometry['margin'], 54)
        self.assertEqual((geometry['presenter_left'], geometry['presenter_top']), (1024, 464))
        composer = Composer(config, geometry)
        side = geometry['diameter']
        np.testing.assert_array_equal(composer.circle_mask, rounded_mask(side, side, side*.25))
        self.assertEqual(composer.circle_mask[20, 20], 1)
        self.assertEqual(rounded_mask(side, side, side*.5)[20, 20], 0)
        camera = np.random.default_rng(42).integers(0, 256, (720, 1280, 3), dtype=np.uint8)
        screen = np.full_like(camera, 230)
        start, outro, transition = config['tutorial_start'], config['outro_start'], config['transition_frames']
        np.testing.assert_array_equal(composer.frame(camera, screen, start-transition, 24), camera)
        np.testing.assert_array_equal(composer.frame(camera, screen, start-1, 24), composer.frame(camera, screen, start, 24))
        np.testing.assert_array_equal(composer.frame(camera, screen, outro, 24), composer.frame(camera, screen, outro-1, 24))
        np.testing.assert_array_equal(composer.frame(camera, screen, outro+transition-1, 24), camera)

    def test_presenter_radius_default_and_validation(self):
        self.assertEqual(self.config()['style']['presenter_corner_radius'], .5)
        for radius in (-.1, .51, float('nan'), float('inf')):
            with self.subTest(radius=radius):
                self.raw['style']['presenter_corner_radius'] = radius
                with self.assertRaises(ValueError):
                    self.config()


@unittest.skipUnless(os.environ.get('TUTORIAL_VIDEO_INTEGRATION') == '1', 'Opt-in local media tests')
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='tutorial-video-editor-test-')
        cls.root = Path(cls.temp.name)
        for name, size, frequency in [('camera', '640x360', 440), ('screen', '600x360', 880)]:
            command = ffmpeg()+['-f', 'lavfi', '-i', f'testsrc2=size={size}:rate=24:duration=3',
                                '-f', 'lavfi', '-i', f'sine=frequency={frequency}:sample_rate=48000:duration=3']
            if name == 'screen':
                command += ['-vf', "select='if(lt(t,1.5),not(mod(n,2)),not(mod(n,3)))'", '-fps_mode', 'vfr']
            command += ['-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
                        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                        '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
                        '-movflags', '+write_colr', '-c:a', 'aac', str(cls.root/f'{name}.mp4')]
            subprocess.run(command, check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def make_config(self, name):
        raw = json.loads((SKILL/'assets/project.example.json').read_text())
        raw.update(fps='12', frames=24, tutorial_start=8, outro_start=16, transition_frames=4,
                   output_dir=name, final_height=720, camera_offset_seconds=.25, screen_offset_seconds=.25)
        raw['audio']['tutorial'] = 'screen.mp4'
        raw['audio']['camera_offset_seconds'] = .25
        raw['audio']['tutorial_offset_seconds'] = .25
        path = self.root/f'{name}.json'
        path.write_text(json.dumps(raw))
        return load(path)

    def test_render_verify_cache_audio_and_final_gate(self):
        config = self.make_config('main')
        config['style']['presenter_corner_radius'] = .25
        report = preflight(config)
        with self.assertRaises(ValueError):
            render(config, report, True, False)
        folder = render(config, report, False, False)
        verified = verify(folder)
        self.assertTrue(verified['decoded_audio_matches'])
        self.assertEqual(verified['geometry']['height'], 720)
        verify(folder)
        with self.assertRaises(ValueError):
            render(config, report, False, False)
        first = prepare_proxies(config, report)
        checksum = fingerprint(first['screen'])
        self.assertEqual(first, prepare_proxies(config, report))
        self.assertEqual(checksum, fingerprint(first['screen']))
        changed = copy.deepcopy(config)
        changed['screen_offset_seconds'] = 0
        second = prepare_proxies(changed, preflight(changed))
        self.assertNotEqual(first['screen'], second['screen'])
        final = render(config, report, True, True)
        self.assertTrue(verify(final, str(folder/'video.mp4'))['full_decode_passed'])
        record = json.loads((folder/'render.json').read_text())
        approved = copy.deepcopy(config)
        approved['revision'] = 'approved-audio'
        approved['audio'] = {'mode': 'approved', 'path': record['soundtrack']}
        approved_report = preflight(approved)
        self.assertTrue(verify(render(approved, approved_report, False, False))['decoded_audio_matches'])

    def test_missing_audio_source_and_tracking_mismatch(self):
        config = self.make_config('negative')
        missing_audio = self.root/'silent.mp4'
        subprocess.run(ffmpeg()+['-i', str(self.root/'screen.mp4'), '-an', '-c:v', 'copy', str(missing_audio)], check=True)
        config['audio']['tutorial'] = str(missing_audio)
        with self.assertRaises(ValueError):
            preflight(config)
        config['audio']['tutorial'] = str(self.root/'screen.mp4')
        config['frames'] = 120
        with self.assertRaises(ValueError):
            preflight(config)
        config['frames'] = 24
        tracking = self.root/'centers.json'
        tracking.write_text(json.dumps({'camera_sha256': 'wrong', 'samples': [[0, .5], [10, .5]]}))
        config['center_samples'] = str(tracking)
        with self.assertRaises(ValueError):
            preflight(config)

    def test_hardware_4k_smoke(self):
        if sys.platform != 'darwin':
            self.skipTest('VideoToolbox smoke test is macOS-only')
        config = self.make_config('hardware')
        config.update(encoder='h264_videotoolbox', final_height=2160,
                      frames=12, tutorial_start=4, outro_start=8, transition_frames=2)
        folder = render(config, preflight(config), True, True)
        self.assertEqual(stream(probe(folder/'video.mp4'), 'video')['height'], 2160)
        self.assertTrue(verify(folder)['full_decode_passed'])


if __name__ == '__main__':
    unittest.main()