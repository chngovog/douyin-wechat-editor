"""Deterministic one-column original-ratio evidence collage, never a cover generator."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont
from integrity import check_frame, check_source, inside, read_json, sha256, write_json


def wrap(draw, text, font, width):
    lines = []; line = ''
    for char in str(text):
        if char == '\n' or (line and draw.textlength(line + char, font=font) > width):
            lines.append(line); line = ''
        if char != '\n':
            line += char
    if line:
        lines.append(line)
    return lines


def build(job_path: Path, spec: dict, font_path: str, width=1200):
    root = job_path.resolve().parent; job = read_json(job_path)
    errors = check_source(job, root)
    if errors:
        raise ValueError('; '.join(errors))
    rows = spec.get('frames', [])
    if not 4 <= len(rows) <= 6:
        raise ValueError('select 4-6 distinct evidence nodes')
    if not spec.get('title') or not spec.get('claim'):
        raise ValueError('collage title and distinct claim required')
    if not 750 <= width <= 2400:
        raise ValueError('width must be 750-2400 pixels')
    title_font = ImageFont.truetype(font_path, round(width * .047))
    label_font = ImageFont.truetype(font_path, round(width * .036))
    pad = round(width * .04); inner = width - pad * 2
    canvas = Image.new('RGB', (width, 10), '#0c141b'); draw = ImageDraw.Draw(canvas)
    header = wrap(draw, spec['title'], title_font, inner)
    height = pad * 2 + len(header) * round(width * .06)
    tiles = []; sources = []; hashes = set()
    for index, row in enumerate(rows, 1):
        if not row.get('label') or not row.get('timestamp'):
            raise ValueError('each frame needs label and timestamp')
        check_frame(job, root, row['path'], row['timestamp'])
        source = inside(root, row['path']); digest = sha256(source)
        if digest in hashes:
            raise ValueError('duplicate image content; do not pad evidence')
        hashes.add(digest)
        with Image.open(source) as raw:
            image = raw.convert('RGB')
        size = (inner, round(image.height * inner / image.width))
        image = image.resize(size, Image.Resampling.LANCZOS)
        label = f'{index} · {row["timestamp"]} | {row["label"]}'
        lines = wrap(draw, label, label_font, inner - pad)
        caption_h = len(lines) * round(width * .049) + pad
        tiles.append((image, lines, caption_h))
        height += image.height + caption_h + pad
        sources.append(dict(path=row['path'], timestamp=row['timestamp'], label=row['label'], sha256=digest))
    canvas = Image.new('RGB', (width, height), '#0c141b'); draw = ImageDraw.Draw(canvas); y = pad
    for line in header:
        draw.text((pad, y), line, font=title_font, fill='#f7f9fa'); y += round(width * .06)
    y += pad
    for image, lines, caption_h in tiles:
        canvas.paste(image, (pad, y)); y += image.height
        draw.rectangle((pad, y, width - pad, y + caption_h), fill='#19232f')
        for idx, line in enumerate(lines):
            draw.text((pad + pad // 2, y + pad // 2 + idx * round(width * .049)), line, font=label_font, fill='#dce5ef')
        y += caption_h + pad
    output = inside(root, spec['output']); manifest = output.with_suffix('.collage.json')
    if output.exists() or manifest.exists():
        raise ValueError('collage exists; use a versioned output name')
    output.parent.mkdir(parents=True, exist_ok=True); canvas.save(output)
    data = dict(kind='video-evidence-collage', layout='single-column-original-ratio',
        title=spec['title'], claim=spec['claim'], source_sha256=job['source']['sha256'],
        frame_count=len(rows), sources=sources, output=spec['output'], output_sha256=sha256(output))
    write_json(manifest, data)
    return output, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', required=True, type=Path); parser.add_argument('--spec', required=True, type=Path)
    parser.add_argument('--font', default=os.environ.get('ARTICLE_FONT')); parser.add_argument('--width', type=int, default=1200)
    args = parser.parse_args()
    try:
        if not args.font:
            raise ValueError('provide --font or ARTICLE_FONT; Chinese font is not bundled')
        output, manifest = build(args.job, read_json(args.spec), args.font, args.width)
        print(f'COLLAGE {output}\nMANIFEST {manifest}')
    except (ValueError, KeyError, OSError) as exc:
        print(f'[FAIL] {exc}', file=sys.stderr); raise SystemExit(2)


if __name__ == '__main__':
    main()
