#!/usr/bin/env python3
"""Repository hygiene check for CI: standard library only.

Fails if a tracked text file or a commit message contains

  * an absolute home-directory path,
  * a chat-session thread identifier of the form used by the maintainers' tooling, or
  * an AI-attribution trailer (co-author, generated-with and similar lines).

Usage:
  python tools/check_hygiene.py                       tracked files only
  python tools/check_hygiene.py --messages A..B       also the messages of commits in A..B
  python tools/check_hygiene.py --messages new        also the commits not on origin/main
                                                      (or every commit when there is no origin/main)

The patterns are assembled from fragments so that this file does not match itself.
"""

from __future__ import annotations

import base64
import binascii
import codecs
import os
import re
import subprocess
import sys

U = "/Us" + "ers/"
HOME = re.compile(r"(?:" + re.escape(U) + r"[A-Za-z0-9._-]+|/ho" + r"me/[a-z][a-z0-9_-]+/|[A-Z]:\\\\Us" + r"ers\\\\)")
THREAD = re.compile(r"\bth" + r"r_[0-9a-z]{8,}\b")
VENDOR = r"(?:cla" + r"ude|anthr" + r"opic|cod" + r"ex|open" + r"ai|cur" + r"sor|copi" + r"lot|chat" + r"gpt|gem" + r"ini)"
TRAILER = re.compile(
    r"(?im)^\s*(?:co-authored-by|generated-by|assisted-by|made-with)\s*:.*" + VENDOR
    + r"|^\s*(?:generated|created|written|made)\s+(?:with|by|using)\s+" + VENDOR
    + r"|^\s*co-authored-by\s*:.*noreply@" + VENDOR
)
TEXT_SUFFIXES = (".md", ".txt", ".py", ".js", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".go", ".rs", ".mod", ".sum", ".lock", ".cfg", ".ini", ".gitignore")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


COMMON_WORDS = frozenset(
    "the and of to in is for with that this not are was be by on as at from or an it its no all can will has have been which when "
    "there their they then than these those into over under about after before between because while where who what".split()
)
QUOTED = re.compile(r"""(["'])((?:(?!\1)[^\n\\]|\\.){40,}?)\1""")
B64 = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")


def english(text):
    words = re.findall(r"[a-z]{2,}", text.lower())
    return sum(word in COMMON_WORDS for word in words), len(words)


def encoded_payloads(label, text, failures):
    """Flag long string literals that look like ROT13 or base64 text (a trivial encoding of hidden content)."""
    for match in QUOTED.finditer(text):
        literal = match.group(2)
        plain_hits, _ = english(literal)
        rot_hits, rot_words = english(codecs.decode(literal, "rot13"))
        if rot_hits >= 2 and rot_hits >= 3 * max(plain_hits, 1) and rot_words >= 5:
            failures.append(f"{label}: ROT13-encoded text in a string literal")
    for match in B64.finditer(text):
        token = match.group(0)
        try:
            decoded = base64.b64decode(token + "=" * (-len(token) % 4), validate=True)
            payload = decoded.decode("utf-8")
        except (binascii.Error, ValueError, UnicodeDecodeError):
            continue
        hits, words = english(payload)
        if payload and sum(ch.isprintable() for ch in payload) / len(payload) > 0.9 and (hits >= 2 or " " in payload):
            failures.append(f"{label}: base64-encoded text")


def check_text(label, text, failures):
    for name, pattern in (("home-directory path", HOME), ("thread identifier", THREAD), ("AI-attribution trailer", TRAILER)):
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            failures.append(f"{label}:{line}: {name}")


def main(argv):
    failures = []
    for path in git("ls-files", "-z").split("\0"):
        if not path or not (path.endswith(TEXT_SUFFIXES) or "." not in path.rsplit("/", 1)[-1]):
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
        check_text(path, text, failures)
    for path in git("ls-files", "-z", "tools").split("\0"):
        if path:
            with open(path, encoding="utf-8", errors="replace") as handle:
                encoded_payloads(path, handle.read(), failures)
    if "--messages" in argv:
        spec = argv[argv.index("--messages") + 1]
        zeros = set(spec.split("..")[0]) <= {"0"} and ".." in spec
        if spec == "new" or zeros:
            try:
                git("rev-parse", "--verify", "-q", "origin/main")
                revs = git("rev-list", "HEAD", "--not", "origin/main").split()
            except subprocess.CalledProcessError:
                revs = git("rev-list", "HEAD").split()
        else:
            revs = git("rev-list", spec).split()
        for rev in revs:
            check_text(f"commit {rev[:12]}", git("log", "-1", "--format=%B", rev), failures)
        # Every version of every tools/ file reachable from the pushed commits.
        seen = {}
        for rev in revs:
            for line in git("ls-tree", "-r", rev, "tools").splitlines():
                info, path = line.split("\t", 1)
                seen.setdefault(info.split()[2], path)
        for oid, path in seen.items():
            encoded_payloads(f"{path} (blob {oid[:12]})", git("cat-file", "blob", oid), failures)
        # Optional: rule-bearing versions of the rewrite tool, identified by a private list.
        rules = os.environ.get("TRACEWEAVE_SCRUB_RULES") or (
            os.path.join(os.environ["TRACEWEAVE_EVAL_DIR"], "private", "public-history-rules.json") if os.environ.get("TRACEWEAVE_EVAL_DIR") else "")
        if rules and os.path.exists(rules):
            import json
            banned = set(json.load(open(rules)).get("drop_tool_blobs", []))
            if banned & set(seen):
                failures.append("a rule-bearing version of the rewrite tool is reachable from the pushed commits")
    if failures:
        print("Hygiene check failed:\n" + "\n".join(failures))
        return 1
    print("PASS: no home-directory paths, thread identifiers or AI-attribution trailers" + (" (tree and commit messages)" if "--messages" in argv else " (tree)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
