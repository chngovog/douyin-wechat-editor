"""Versioned editorial defaults; local estimates, never platform guarantees."""
from __future__ import annotations

from html.parser import HTMLParser
import re

WORD_POLICY = 'wechat-visible-text-400-500-2026-10-13'
VISUAL_POLICY = 'two-annotated-collages-2026-10-11'
FRAME_POLICY = 'compact-2-4-2026-10-12'
DELIVERY_POLICY = 'article-and-two-covers-2026-10-12'
EDITORIAL_POLICY = 'substantive-value-and-voice-2026-10-12'


class VisibleText(HTMLParser):
    """Extract our renderer's main content, not tags, alt, metadata or scripts."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = {k: [] for k in ('title', 'body', 'captions', 'byline', 'sources')}

    def handle_starttag(self, tag, attrs):
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append((tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        tags = {t for t, _ in self.stack}
        if 'main' not in tags or tags.intersection({'script', 'style', 'template'}):
            return
        classes = {c for _, a in self.stack for c in a.get('class', '').split()}
        kind = ('title' if 'h1' in tags else 'sources' if 'sources' in classes
                else 'byline' if 'byline' in classes else 'captions' if 'figcaption' in tags else 'body')
        self.parts[kind].append(data)


def extract_text(html):
    parser = VisibleText()
    parser.feed(html)
    return {k: re.sub(r'\s+', '', ''.join(v)) for k, v in parser.parts.items()}


def count_report(actual, expected):
    parts = extract_text(actual)
    counts = {k: len(v) for k, v in parts.items()}
    body = sum(v for k, v in counts.items() if k != 'title')
    return {
        'policy': WORD_POLICY, 'scope': 'local visible-character estimate; not verified in WeChat',
        'body_visible_chars': body, 'copy_all_visible_chars': body + counts['title'],
        'breakdown': counts, 'cjk_reference_only': len(re.findall(r'[\u4e00-\u9fff]', ''.join(parts.values()))),
        'text_matches_job': parts == extract_text(expected), 'wechat_editor_count': None,
    }


def count_errors(report):
    errors = []
    if not 400 <= report['body_visible_chars'] <= 500:
        errors.append(f"complete body must be 400-500 visible characters: {report['body_visible_chars']}")
    if report['copy_all_visible_chars'] > 500:
        errors.append(f"including H1 exceeds 500: {report['copy_all_visible_chars']}")
    if not report['text_matches_job']:
        errors.append('HTML text differs from current job; render again')
    return errors
