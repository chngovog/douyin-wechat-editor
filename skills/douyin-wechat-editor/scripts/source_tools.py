"""Inspect dependencies, bind an authorized local video, and extract proof frames."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from integrity import check_source, inside, read_json, seconds, sha256, write_json


def binary(name):
    value = os.environ.get(name.upper()) or shutil.which(name)
    if not value:
        raise ValueError(f'{name} missing; set {name.upper()} or PATH')
    return value


def doctor(_args):
    statuses = {'python': sys.executable, 'pillow': bool(importlib.util.find_spec('PIL'))}
    for name in ('ffmpeg', 'ffprobe', 'node'):
        statuses[name] = os.environ.get(name.upper()) or shutil.which(name) or 'MISSING'
    statuses['browser_exe'] = os.environ.get('BROWSER_EXE', 'Playwright managed Chromium')
    statuses['font'] = os.environ.get('ARTICLE_FONT', 'provide --font for Chinese collage labels')
    if statuses['node'] != 'MISSING':
        probe = subprocess.run([statuses['node'], '-e', "console.log(require.resolve('playwright'))"],
                               cwd=Path(__file__).parent, capture_output=True, text=True)
        statuses['playwright'] = probe.stdout.strip() if probe.returncode == 0 else 'MISSING'
    print(json.dumps(statuses, ensure_ascii=False, indent=2))
    print('Browser control, ImageGen, ASR and rights require separate runtime checks; not tested here.')
    if not statuses['pillow'] or any(v == 'MISSING' for v in statuses.values()):
        raise SystemExit(2)


def bind(args):
    job_path = Path(args.job).resolve(); root = job_path.parent
    job = read_json(job_path); video = inside(root, args.video)
    result = subprocess.run([binary('ffprobe'), '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type', '-of', 'json', str(video)],
        check=True, capture_output=True, text=True)
    probe = json.loads(result.stdout)
    if not any(s.get('codec_type') == 'video' for s in probe.get('streams', [])):
        raise ValueError('source has no video stream')
    digest = sha256(video)
    old = job.get('identity', {}).get('source_sha256')
    if old and old != digest:
        raise ValueError('different source: initialize a new task; old evidence cannot be rebound')
    source = job['source']
    source.update(path=video.relative_to(root).as_posix(), sha256=digest,
                  duration_seconds=float(probe['format']['duration']))
    job['identity'] = dict(account=job['account'], slug=job['slug'], source_sha256=digest)
    job['originality']['source_duration_seconds'] = source['duration_seconds']
    write_json(job_path, job)
    print(f'BOUND {video.name} | {source["duration_seconds"]:.3f}s | sha256={digest}')


def frame(args):
    job_path = Path(args.job).resolve(); root = job_path.parent; job = read_json(job_path)
    errors = check_source(job, root)
    if errors:
        raise ValueError('; '.join(errors))
    stamp = seconds(args.at)
    if stamp >= job['source']['duration_seconds']:
        raise ValueError('timestamp must precede video end')
    output = inside(root, args.output)
    if output.exists() or output.with_suffix('.frame.json').exists():
        raise ValueError('frame exists; choose a versioned filename')
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([binary('ffmpeg'), '-v', 'error', '-nostdin', '-ss', str(stamp),
        '-i', str(inside(root, job['source']['path'])), '-frames:v', '1', '-an', '-n', str(output)], check=True)
    write_json(output.with_suffix('.frame.json'), dict(kind='source-video-frame',
        path=output.relative_to(root).as_posix(), seconds=stamp, timestamp=args.at,
        source_sha256=job['source']['sha256'], sha256=sha256(output)))
    print(f'FRAME {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('doctor'); p.set_defaults(func=doctor)
    p = sub.add_parser('bind'); p.add_argument('job'); p.add_argument('--video', required=True); p.set_defaults(func=bind)
    p = sub.add_parser('frame'); p.add_argument('job'); p.add_argument('--at', required=True); p.add_argument('--output', required=True); p.set_defaults(func=frame)
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print(f'[FAIL] {exc}', file=sys.stderr); raise SystemExit(2)


if __name__ == '__main__':
    main()
