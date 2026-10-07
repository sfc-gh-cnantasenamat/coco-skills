"""CLI: preflight, prepare, render, verify. Read SKILL.md before final rendering."""
import argparse
from fractions import Fraction
from pathlib import Path
import json
import subprocess
import tempfile

from compose import Composer
from media import Reader, filters, prepare_audio, prepare_proxies
from project import encode_flags, ffmpeg, fingerprint, load, preflight, probe, require, stream, write_json


def render(config, report, final, approved):
    require(not final or approved, 'Final rendering requires user approval and --final-approved')
    height = config['final_height'] if final else config['proxy_height']
    output_root = Path(config['output_dir'])
    output_root.mkdir(parents=True, exist_ok=True)
    folder = output_root/f'{config["revision"]}-{"final" if final else "proxy"}-{height}p'
    require(not folder.exists(), f'Output already exists: {folder}. Use a new revision.')
    proxies = None if final else prepare_proxies(config, report)
    soundtrack = prepare_audio(config, report)
    geometry = report['final_layout' if final else 'proxy_layout']
    composer = Composer(config, geometry, report.get('center_samples'))
    folder.mkdir()
    target = folder/'video.mp4'
    readers, encoder = [], None
    errors = tempfile.TemporaryFile()
    completed = False
    try:
        for name in ('camera', 'screen'):
            chain, width, height = filters(config, name, geometry)
            readers.append(Reader(config[name] if final else proxies[name], width, height,
                                  config['frames'], chain if final else None))
        command = ffmpeg()+['-f', 'rawvideo', '-pix_fmt', 'bgr24',
                            '-s', f'{geometry["width"]}x{geometry["height"]}', '-r', config['fps'], '-i', 'pipe:0',
                            '-i', str(soundtrack), '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'copy',
                            '-vf', 'scale=out_color_matrix=bt709']
        command += encode_flags(config['encoder'], final)+[str(target)]
        encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors)
        fps = float(Fraction(config['fps']))
        for frame_index in range(config['frames']):
            result = composer.frame(readers[0].read(), readers[1].read(), frame_index, fps)
            encoder.stdin.write(result.tobytes())
            if frame_index % 240 == 0:
                print(f'{frame_index}/{config["frames"]}', flush=True)
        encoder.stdin.close()
        require(encoder.wait(timeout=120) == 0, 'Encoder failed')
        for reader in readers:
            reader.close(success=True)
        readers.clear()
        video = stream(probe(target), 'video')
        require(all(video.get(tag) == 'bt709' for tag in ('color_space', 'color_transfer', 'color_primaries')),
                'BT.709 metadata missing; preserve export and inspect encoder metadata')
        write_json(folder/'render.json', {'config': config, 'preflight': report,
                                         'geometry': geometry, 'final': final,
                                         'soundtrack': str(soundtrack), 'soundtrack_sha256': fingerprint(soundtrack),
                                         'video_sha256': fingerprint(target)})
        completed = True
    finally:
        for reader in readers:
            try:
                reader.close()
            except Exception as error:
                print(f'Decoder cleanup: {error}', flush=True)
        if encoder is not None and encoder.poll() is None:
            encoder.terminate()
            try:
                encoder.wait(timeout=20)
            except subprocess.TimeoutExpired:
                encoder.kill()
                encoder.wait()
        if not completed:
            errors.seek(0)
            print(errors.read().decode(errors='replace'), flush=True)
        errors.close()
    print(target, flush=True)
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='action', required=True)
    for action in ('preflight', 'prepare', 'render'):
        subparser = subparsers.add_parser(action)
        subparser.add_argument('--config', required=True)
        if action == 'render':
            subparser.add_argument('--final', action='store_true')
            subparser.add_argument('--final-approved', action='store_true')
    verifier = subparsers.add_parser('verify')
    verifier.add_argument('--render-dir', required=True)
    verifier.add_argument('--approved-proxy', help='Optional video.mp4 from approved proxy')
    args = parser.parse_args()
    if args.action == 'verify':
        from verify import verify
        verify(Path(args.render_dir).resolve(), args.approved_proxy)
        return
    config = load(args.config)
    if args.action == 'render':
        require(not args.final or args.final_approved, 'Ask for final approval before --final --final-approved')
    report = preflight(config)
    if args.action == 'preflight':
        print(json.dumps(report, indent=2))
    elif args.action == 'prepare':
        print(prepare_proxies(config, report))
        print(prepare_audio(config, report))
    else:
        render(config, report, args.final, args.final_approved)


if __name__ == '__main__':
    main()