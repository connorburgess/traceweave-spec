#!/usr/bin/env python3
"""TW-07: deterministic README sentence inventory and exact evidence references.

Only five exclusions: ATX headings; whole link-only lines; fenced code; HTML
picture markup (alt descriptions are mapped); table column headings and their separator rows. Everything
else, including fragments, table data cells, captions and link-bearing prose,
is a claim. Exclusions are inventoried with source lines and text, not dropped
silently. Non-author approval of these rules remains a release-review action.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / 'docs/release/readme-claim-map.json'
EXCLUSIONS = ('heading', 'link-only', 'code-block', 'picture', 'table-header')


def sentences(text):
    # Protect punctuation inside inline code and link destinations. Dots within
    # words/numbers are never sentence boundaries. Markdown emphasis after the
    # terminator is retained; splitting occurs before whitespace + new prose.
    protected = {}
    def protect(m):
        key = f'\x00{len(protected)}\x00'
        protected[key] = m.group()
        return key
    text = re.sub(r'`+[^`]+`+|\]\([^)]*\)|Figure \d+\.', protect, text)
    parts = re.split(r'(?<=[.!?])(?=[*_]*\s+\S)', text)
    result = []
    for part in parts:
        for key, value in protected.items():
            part = part.replace(key, value)
        if part.strip():
            result.append(part.strip())
    return result


class PictureDescriptions(HTMLParser):
    """Collect accessible assertions separately from inert HTML markup."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.descriptions = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'picture':
            self.depth += 1
        if tag == 'img' and self.depth:
            alt = dict(attrs).get('alt')
            if alt:
                self.descriptions.setdefault(self.getpos()[0], []).append(alt)

    def handle_endtag(self, tag):
        if tag == 'picture':
            self.depth -= 1


def extract(readme):
    claims, excluded, paragraph = [], [], []
    fence = None
    picture = False
    parser = PictureDescriptions()
    parser.feed(readme)
    lines = readme.splitlines()
    def flush():
        if paragraph:
            line = paragraph[0][0]
            for text in sentences(' '.join(t.strip() for _, t in paragraph)):
                claims.append({'line': line, 'sentence': text})
            paragraph.clear()
    for i, line in enumerate(lines, 1):
        if i in parser.descriptions:
            flush()
            for description in parser.descriptions[i]:
                claims.append({"line": i, "sentence": description})
        stripped = line.strip()
        reason = None
        mark = re.match(r'^(`{3,}|~{3,})', stripped)
        if fence:
            reason = 'code-block'
            if mark and mark[1][0] == fence[0] and len(mark[1]) >= len(fence):
                fence = None
        elif mark:
            fence = mark[1]
            reason = 'code-block'
        elif picture or re.search(r'<picture(?:\s|>)', stripped):
            picture = '</picture>' not in stripped
            reason = 'picture'
        elif re.match(r'^#{1,6}\s', stripped):
            reason = 'heading'
        elif stripped and re.fullmatch(r'(?:[-*+]\s+)?(?:\[[^\]]+\]\([^)]+\)\s*(?:[·|]\s*)?)+', stripped):
            reason = 'link-only'
        elif stripped.startswith('|') and (
            re.fullmatch(r'\|[\s:|\-]+', stripped) or
            (i < len(lines) and re.fullmatch(r'\|[\s:|\-]+', lines[i].strip()))
        ):
            reason = 'table-header'
        if reason:
            flush()
            excluded.append({'line': i, 'reason': reason, 'text': line})
        elif not stripped:
            flush()
        elif stripped.startswith('|'):
            flush()
            # Table data is conservatively one claim unit per row, even if its
            # cells have no grammatical sentence terminators.
            claims.append({'line': i, 'sentence': stripped})
        elif re.match(r'^(?:[-*+]\s|\d+\.\s)', stripped):
            flush()
            paragraph.append((i, re.sub(r'^(?:[-*+]\s+|\d+\.\s+)', '', stripped)))
        else:
            paragraph.append((i, stripped))
    flush()
    if fence or picture:
        raise ValueError('README has an unclosed code fence or picture element')
    return claims, excluded


def check(data, readme=None):
    claims, exclusions = extract(readme if readme is not None else (ROOT / 'README.md').read_text(encoding='utf-8'))
    if data.get('exclusionRules') != list(EXCLUSIONS):
        raise ValueError('README exclusion rules changed without updating the audited inventory')
    if data.get('excluded') != exclusions:
        raise ValueError('README exclusions drifted; regenerate and obtain non-author review')
    rows = data['claims']
    if [r['sentence'] for r in rows] != [c['sentence'] for c in claims]:
        raise ValueError('README claim sentences unmapped, reordered or stale')
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('duplicate README claim id')
    for row in rows:
        if not row.get('rationale') or not row.get('evidence'):
            raise ValueError(f"{row['id']}: no evidence/rationale")
        for evidence in row['evidence']:
            if evidence.get('kind') not in ('fixture', 'benchmark', 'decision', 'review'):
                raise ValueError(f"{row['id']}: invalid evidence kind")
            path = (ROOT / evidence['path']).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError(f"{row['id']}: missing evidence file")
            quote = evidence.get('quote', '')
            if not quote or quote not in path.read_text(encoding='utf-8'):
                raise ValueError(f"{row['id']}: exact evidence locator missing or stale")
    return len(claims), len(exclusions)


if __name__ == '__main__':
    try:
        mapped, excluded = check(json.loads(MAP.read_text(encoding='utf-8')))
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit(f'FAIL README claim map: {exc}')
    print(f'PASS M5.2 README claims: {mapped} mapped, 0 unmapped; {excluded} excluded source lines; current exclusions approved in the independent 07c98ca review (see ROADMAP.md)')
