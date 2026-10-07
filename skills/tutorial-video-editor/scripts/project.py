"""Configuration, read-only preflight, geometry, and media utilities."""
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import math
import re
import shutil
import subprocess


def require(condition, message):
    if not condition:
        raise ValueError(message)


def tool(name):
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f'{name} not found on PATH')
    return found


def run(arguments):
    subprocess.run(arguments, check=True)


def probe(path):
    return json.loads(subprocess.check_output([
        tool('ffprobe'), '-v', 'error', '-show_streams', '-show_format',
        '-of', 'json', str(path),
    ]))


def stream(info, kind):
    matches = [item for item in info['streams'] if item['codec_type'] == kind]
    require(len(matches) == 1, f'Expected exactly one {kind} stream; found {len(matches)}')
    return matches[0]


def duration(info, media):
    return float(media.get('duration', info['format'].get('duration', 0)))


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def key_for(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]


def write_json(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2)


def canvas(height):
    return 2*round(height*16/9/2), height


def layout(config, height, screen_ratio):
    width, height = canvas(height)
    style = config['style']
    inset = round(height*style['screen_inset'])
    available_width, available_height = width-2*inset, height-2*inset
    screen_height = 2*math.floor(min(available_height, available_width/screen_ratio)/2)
    screen_width = 2*math.floor(screen_height*screen_ratio/2)
    diameter = round(height*style['presenter_diameter'])
    margin = round(height*style['presenter_margin'])
    require(0 < screen_width <= available_width and 0 < screen_height <= available_height,
            'Screencast does not fit the configured inset')
    require(diameter >= 2 and margin >= 0 and diameter+2*margin <= min(width, height),
            'Presenter diameter or margin does not fit canvas')
    return dict(width=width, height=height, screen_width=screen_width,
                screen_height=screen_height, screen_left=(width-screen_width)//2,
                screen_top=(height-screen_height)//2, diameter=diameter, margin=margin,
                presenter_left=width-margin-diameter, presenter_top=height-margin-diameter)


def load(path):
    path = Path(path).expanduser().resolve()
    config = json.loads(path.read_text())
    require(config.get('version') == 1, 'Expected configuration version 1')
    allowed = {'version', 'camera', 'screen', 'camera_offset_seconds', 'screen_offset_seconds',
               'fps', 'frames', 'tutorial_start', 'outro_start', 'transition_frames',
               'proxy_height', 'final_height', 'output_dir', 'revision', 'encoder',
               'assume_bt709_for_untagged', 'audio', 'style', 'center_samples'}
    require(not set(config)-allowed, f'Unknown settings: {set(config)-allowed}')
    defaults = dict(fps='24000/1001', proxy_height=720, final_height=2160,
                    transition_frames=30, camera_offset_seconds=0, screen_offset_seconds=0,
                    encoder='libx264', assume_bt709_for_untagged=False)
    config = defaults | config
    config['fps'] = str(Fraction(str(config['fps'])))
    require(0 < Fraction(config['fps']) <= 120, 'FPS must be positive and <= 120')
    for name in ('frames', 'tutorial_start', 'outro_start', 'transition_frames', 'proxy_height', 'final_height'):
        require(type(config[name]) is int, f'{name} must be an integer')
    require(config['frames'] > 0, 'frames must be positive')
    transition = config['transition_frames']
    require(2 <= transition <= config['tutorial_start'] < config['outro_start']
            and config['outro_start']+transition <= config['frames'], 'Invalid segment boundaries')
    require(config['proxy_height'] in (480, 720), 'proxy_height must be 480 or 720')
    require(config['final_height'] in (720, 1080, 1440, 2160), 'Unsupported final_height')
    require(config['encoder'] in ('libx264', 'h264_videotoolbox'), 'Unsupported encoder')
    require(bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', config['revision'])), 'Unsafe revision name')
    def local(value):
        result = Path(value).expanduser()
        return str((path.parent/result).resolve())
    for name in ('camera', 'screen', 'output_dir'):
        config[name] = local(config[name])
    for name in ('camera_offset_seconds', 'screen_offset_seconds'):
        require(math.isfinite(config[name]) and config[name] >= 0, f'{name} must be nonnegative')
    style_defaults = dict(screen_inset=0, corner_radius=0,
                          presenter_diameter=192/720, presenter_margin=36/720,
                          presenter_corner_radius=.5,
                          body_center_x=.5, background_colors=['#00FFFF', '#9810FA'])
    style = config.get('style', {})
    require(not set(style)-set(style_defaults)-{'background_image'}, 'Unknown style setting')
    config['style'] = style_defaults | style
    for name in ('screen_inset', 'corner_radius', 'presenter_diameter', 'presenter_margin', 'presenter_corner_radius', 'body_center_x'):
        value = config['style'][name]
        require(math.isfinite(value) and 0 <= value <= 1, f'Invalid style {name}')
    require(config['style']['presenter_corner_radius'] <= .5, 'presenter_corner_radius must be <= .5')
    require(config['style']['screen_inset'] < .5, 'screen_inset must be less than .5')
    colors = config['style']['background_colors']
    require(len(colors) == 2 and all(re.fullmatch(r'#[0-9A-Fa-f]{6}', color) for color in colors),
            'Provide two #RRGGBB background colors')
    if style.get('background_image'):
        config['style']['background_image'] = local(style['background_image'])
    if config.get('center_samples'):
        config['center_samples'] = local(config['center_samples'])
    audio = config['audio']
    require(audio.get('mode') in ('approved', 'segments'), 'audio.mode must be approved or segments')
    if audio['mode'] == 'approved':
        require(set(audio) <= {'mode', 'path'}, 'Unknown approved audio setting')
        audio['path'] = local(audio['path'])
    else:
        require(set(audio) <= {'mode', 'camera', 'tutorial', 'camera_offset_seconds', 'tutorial_offset_seconds'},
                'Unknown segment audio setting')
        for name in ('camera', 'tutorial'):
            audio[name] = local(audio[name])
            offset = audio.setdefault(name+'_offset_seconds', 0)
            require(math.isfinite(offset) and offset >= 0, 'Audio offsets must be nonnegative')
    return config


def preflight(config):
    tool('ffmpeg')
    encoders = subprocess.check_output([tool('ffmpeg'), '-hide_banner', '-encoders'], text=True)
    require(any(config['encoder'] in line.split() for line in encoders.splitlines()),
            f'Encoder unavailable: {config["encoder"]}')
    seconds = config['frames']/float(Fraction(config['fps']))
    report = {'duration': seconds, 'sources': {}, 'warnings': []}
    for name in ('camera', 'screen'):
        source = Path(config[name])
        require(source.is_file(), f'Missing {name}: {source}')
        info = probe(source)
        video = stream(info, 'video')
        require(video.get('sample_aspect_ratio', '1:1') in ('1:1', 'N/A'), 'Normalize non-square pixels first')
        rotations = [item.get('rotation', 0) for item in video.get('side_data_list', [])]
        require(not any(rotations) and not float(video.get('tags', {}).get('rotate', 0)),
                'Normalize rotated video first')
        require(video.get('color_transfer') not in ('smpte2084', 'arib-std-b67'), 'HDR requires explicit tone mapping')
        for tag in ('color_space', 'color_transfer', 'color_primaries'):
            value = video.get(tag, 'unknown')
            require(value == 'bt709' or (value in ('unknown', 'unspecified') and config['assume_bt709_for_untagged']),
                    f'{name} {tag}={value}; review and normalize or explicitly acknowledge untagged SDR')
        needed = seconds+config[name+'_offset_seconds']
        require(duration(info, video)+.2 >= needed, f'{name} is too short for edit and offset')
        report['sources'][name] = {'video': video, 'sha256': fingerprint(source)}
        if video['height'] < config['final_height']:
            report['warnings'].append(f'{name} is smaller than final canvas height; inspect scaling quality')
    ratio = report['sources']['screen']['video']['width']/report['sources']['screen']['video']['height']
    report['proxy_layout'] = layout(config, config['proxy_height'], ratio)
    report['final_layout'] = layout(config, config['final_height'], ratio)
    background = config['style'].get('background_image')
    if background:
        from PIL import Image
        with Image.open(background) as image:
            image.verify()
    audio = config['audio']
    fps = float(Fraction(config['fps']))
    audio_sources = [(audio['path'], seconds, True)] if audio['mode'] == 'approved' else [
        (audio['camera'], seconds+audio['camera_offset_seconds'], False),
        (audio['tutorial'], config['outro_start']/fps+audio['tutorial_offset_seconds'], False)]
    report['audio_sources'] = []
    for source, needed, approved in audio_sources:
        info = probe(source)
        media = stream(info, 'audio')
        available = duration(info, media)
        require(available+.025 >= needed, f'Audio too short: {source}')
        if approved:
            require(media['codec_name'] == 'aac', 'Approved soundtrack must be AAC for lossless MP4 stream copy')
            require(abs(available-needed) <= .1, 'Approved soundtrack duration must match edit')
        report['audio_sources'].append({'path': source, 'sha256': fingerprint(source)})
    if config.get('center_samples'):
        samples = json.loads(Path(config['center_samples']).read_text())
        require(samples['camera_sha256'] == report['sources']['camera']['sha256'], 'Tracking belongs to another camera source')
        points = samples['samples']
        require(len(points) >= 2 and points[0][0] <= 0 and points[-1][0] >= (config['frames']-1)/fps,
                'Tracking must cover the output timeline')
        require(all(len(point) == 2 and all(math.isfinite(value) for value in point)
                    and 0 <= point[1] <= 1 for point in points), 'Invalid tracking sample')
        require(all(first[0] < second[0] for first, second in zip(points, points[1:])), 'Tracking times must increase')
        report['center_samples'] = points
    return report


def ffmpeg():
    return [tool('ffmpeg'), '-nostdin', '-v', 'error', '-n']


def encode_flags(encoder, final=False):
    flags = ['-c:v', encoder]
    flags += ['-preset', 'veryfast', '-crf', '18' if final else '23'] if encoder == 'libx264' else ['-b:v', '45M' if final else '3M']
    return flags+['-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                  '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart+write_colr',
                  '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1']