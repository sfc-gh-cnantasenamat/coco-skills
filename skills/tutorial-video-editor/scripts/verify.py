"""Full decoding, audio identity, metadata, and sampled visual evidence."""
from fractions import Fraction
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import uuid

import cv2
import numpy as np
from PIL import Image, ImageDraw

from project import duration, ffmpeg, fingerprint, probe, require, run, stream, write_json


def audio_hash(path):
    return subprocess.check_output(ffmpeg()+['-i', str(path), '-map', '0:a:0', '-c:a', 'pcm_s16le',
                                            '-f', 'hash', '-hash', 'sha256', '-'], text=True).strip()


def verify(folder, approved_proxy=None):
    record = json.loads((folder/'render.json').read_text())
    config, geometry = record['config'], record['geometry']
    target = folder/'video.mp4'
    require(fingerprint(target) == record['video_sha256'], 'Video changed since rendering')
    require(fingerprint(record['soundtrack']) == record['soundtrack_sha256'], 'Soundtrack changed since rendering')
    info = probe(target)
    video, audio = stream(info, 'video'), stream(info, 'audio')
    require((video['width'], video['height']) == (geometry['width'], geometry['height']), 'Wrong output dimensions')
    require(video['codec_name'] == 'h264' and video['pix_fmt'] == 'yuv420p', 'Unexpected video encoding')
    require(Fraction(video['avg_frame_rate']) == Fraction(config['fps']), 'Wrong FPS')
    require(int(video['nb_frames']) == config['frames'], 'Wrong frame count')
    require(abs(float(video['duration'])-record['preflight']['duration']) < .002, 'Wrong duration')
    require(all(video.get(tag) == 'bt709' for tag in ('color_space', 'color_transfer', 'color_primaries')),
            'Incomplete color metadata')
    require(audio['codec_name'] == 'aac', 'Expected AAC audio')
    require(abs(duration(info, audio)-record['preflight']['duration']) < .1, 'Audio duration mismatch')
    require(audio_hash(target) == audio_hash(record['soundtrack']), 'Decoded audio differs from soundtrack')
    run(ffmpeg()+['-xerror', '-i', str(target), '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'])
    if approved_proxy:
        proxy_video = stream(probe(approved_proxy), 'video')
        require(Fraction(proxy_video['avg_frame_rate']) == Fraction(config['fps'])
                and int(proxy_video['nb_frames']) == config['frames'], 'Proxy timeline mismatch')
    start, outro, transition = config['tutorial_start'], config['outro_start'], config['transition_frames']
    indices = sorted(set([0, start-transition, start-transition//2, start-1, start,
                          (start+outro)//2, outro-1, outro, outro+transition//2,
                          outro+transition-1, min(outro+transition, config['frames']-1), config['frames']-1]))
    evidence = folder/f'verification-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")}-{uuid.uuid4().hex[:8]}'
    evidence.mkdir()
    sheet = Image.new('RGB', (960, ((len(indices)+1)//2)*300), '#202020')
    draw = ImageDraw.Draw(sheet)
    capture = cv2.VideoCapture(str(target))
    proxy_capture = cv2.VideoCapture(str(approved_proxy)) if approved_proxy else None
    comparisons = []
    try:
        for index, frame_index in enumerate(indices):
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            require(ok, f'Cannot read frame {frame_index}')
            if proxy_capture:
                proxy_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ok, reference = proxy_capture.read()
                require(ok, f'Cannot read proxy frame {frame_index}')
                reduced = cv2.resize(frame, (reference.shape[1], reference.shape[0]), interpolation=cv2.INTER_AREA)
                error = float(np.abs(reduced.astype(float)-reference.astype(float)).mean())
                require(error < 15, f'Visual comparison failed at {frame_index}: {error}')
                comparisons.append({'frame': frame_index, 'mean_absolute_error': error})
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            left, top = index % 2*480, index//2*300
            sheet.paste(image.resize((480, 270)), (left, top+25))
            draw.text((left+8, top+5), f'Frame {frame_index}', fill='white')
            if frame_index == start:
                image.save(evidence/'tutorial.png')
        sheet.save(evidence/'contact-sheet.jpg', quality=92)
    finally:
        capture.release()
        if proxy_capture:
            proxy_capture.release()
    report = {'video': str(target), 'metadata': info, 'full_decode_passed': True,
              'decoded_audio_matches': True, 'comparisons': comparisons,
              'visual_review_required': True, 'geometry': geometry}
    write_json(evidence/'report.json', report)
    print(f'PASS: metadata, audio identity, full decode, sampled frames. Review {evidence}', flush=True)
    return report