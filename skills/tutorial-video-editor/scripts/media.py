"""Cached derivatives and finite sequential decoding; no network access."""
from fractions import Fraction
from pathlib import Path
import json
import subprocess
import tempfile

import numpy as np

from project import encode_flags, ffmpeg, fingerprint, key_for, probe, require, run, stream, write_json


def filters(config, name, geometry):
    # Offsets mean source time = output time + offset, on the normalized source timeline.
    offset = config[name+'_offset_seconds']
    normalize = f'setpts=PTS-STARTPTS,trim=start={offset},setpts=PTS-STARTPTS,fps={config["fps"]}'
    if name == 'camera':
        width, height = geometry['width'], geometry['height']
        sizing = f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}'
    else:
        width, height = geometry['screen_width'], geometry['screen_height']
        sizing = f'scale={width}:{height}'
    return f'{normalize},{sizing},setsar=1,tpad=stop_mode=clone:stop_duration=0.2', width, height


def cache_directory(config, label, identity):
    root = Path(config['output_dir'])/'cache'
    root.mkdir(parents=True, exist_ok=True)
    folder = root/f'{label}-{key_for(identity)}'
    marker = folder/'complete.json'
    if folder.exists():
        require(marker.is_file(), f'Incomplete cache: {folder}. Preserve it and use a fresh output_dir after investigating.')
        record = json.loads(marker.read_text())
        require(record['identity'] == identity, 'Cache identity mismatch')
        for filename, checksum in record['files'].items():
            require(fingerprint(folder/filename) == checksum, f'Cache content changed: {folder/filename}')
        return folder, True
    folder.mkdir()
    return folder, False


def finish_cache(folder, identity, paths):
    write_json(folder/'complete.json', {'identity': identity,
                                      'files': {path.name: fingerprint(path) for path in paths}})


def prepare_proxies(config, report):
    geometry = report['proxy_layout']
    identity = {'recipe': 1, 'fps': config['fps'], 'frames': config['frames'],
                'encoder': config['encoder'], 'geometry': geometry,
                'sources': {name: {'sha256': report['sources'][name]['sha256'],
                                   'offset': config[name+'_offset_seconds']} for name in ('camera', 'screen')}}
    folder, cached = cache_directory(config, 'proxy', identity)
    paths = {name: folder/f'{name}.mp4' for name in ('camera', 'screen')}
    if not cached:
        for name, target in paths.items():
            chain, _, _ = filters(config, name, geometry)
            run(ffmpeg()+['-threads', '2', '-i', config[name], '-map', '0:v:0', '-an',
                          '-vf', chain+',scale=out_color_matrix=bt709',
                          '-frames:v', str(config['frames'])]+encode_flags(config['encoder'])+[str(target)])
            video = stream(probe(target), 'video')
            require(int(video['nb_frames']) == config['frames'], f'Short proxy: {target}')
        finish_cache(folder, identity, list(paths.values()))
    return paths


def prepare_audio(config, report):
    if config['audio']['mode'] == 'approved':
        return Path(config['audio']['path'])
    identity = {'recipe': 1, 'audio': config['audio'], 'sources': report['audio_sources'],
                'fps': config['fps'], 'frames': config['frames'],
                'tutorial_start': config['tutorial_start'], 'outro_start': config['outro_start']}
    folder, cached = cache_directory(config, 'audio', identity)
    target = folder/'soundtrack.m4a'
    if cached:
        return target
    fps = float(Fraction(config['fps']))
    intro = config['tutorial_start']/fps
    outro = config['outro_start']/fps
    end = config['frames']/fps
    audio = config['audio']
    camera_offset, tutorial_offset = audio['camera_offset_seconds'], audio['tutorial_offset_seconds']
    chain = (
        '[0:a:0]asetpts=PTS-STARTPTS,asplit=2[camintro][camoutro];'
        f'[camintro]atrim=start={camera_offset}:end={camera_offset+intro},asetpts=PTS-STARTPTS,'
        'aresample=48000,aformat=channel_layouts=stereo[intro];'
        f'[1:a:0]asetpts=PTS-STARTPTS,atrim=start={tutorial_offset+intro}:end={tutorial_offset+outro},'
        'asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[tutorial];'
        f'[camoutro]atrim=start={camera_offset+outro}:end={camera_offset+end},asetpts=PTS-STARTPTS,'
        'aresample=48000,aformat=channel_layouts=stereo[outro];'
        '[intro][tutorial][outro]concat=n=3:v=0:a=1[audio]'
    )
    run(ffmpeg()+['-i', audio['camera'], '-i', audio['tutorial'], '-filter_complex', chain,
                  '-map', '[audio]', '-c:a', 'aac', '-b:a', '256k', str(target)])
    finish_cache(folder, identity, [target])
    return target


class Reader:
    def __init__(self, path, width, height, count, chain=None):
        self.shape = (height, width, 3)
        self.size = width*height*3
        self.count = count
        self.read_count = 0
        self.errors = tempfile.TemporaryFile()
        command = ffmpeg()+['-threads', '2', '-i', str(path), '-map', '0:v:0', '-an']
        if chain:
            command += ['-vf', chain]
        command += ['-frames:v', str(count), '-threads', '2', '-f', 'rawvideo', '-pix_fmt', 'bgr24', 'pipe:1']
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=self.errors)

    def read(self):
        chunks, remaining = [], self.size
        while remaining:
            chunk = self.process.stdout.read(remaining)
            if not chunk:
                raise RuntimeError(f'Decoder ended at frame {self.read_count}; expected {self.count}')
            chunks.append(chunk)
            remaining -= len(chunk)
        self.read_count += 1
        return np.frombuffer(b''.join(chunks), np.uint8).reshape(self.shape)

    def close(self, success=False):
        try:
            if not success and self.process.poll() is None:
                self.process.terminate()
            self.process.stdout.close()
            try:
                status = self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
                raise RuntimeError('Decoder did not exit')
            self.errors.seek(0)
            details = self.errors.read().decode(errors='replace')
            if success and (status or self.read_count != self.count):
                raise RuntimeError(f'Decoder failed ({status}): {details}')
        finally:
            self.errors.close()