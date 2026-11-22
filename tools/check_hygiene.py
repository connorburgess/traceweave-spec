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
    if failures:
        print("Hygiene check failed:\n" + "\n".join(failures))
        return 1
    print("PASS: no home-directory paths, thread identifiers or AI-attribution trailers" + (" (tree and commit messages)" if "--messages" in argv else " (tree)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
