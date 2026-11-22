#!/usr/bin/env python3
"""Generic history scrubber and scanner. Standard library only.

This tool contains no rules. The substitution rules and detectors live in a
private JSON file outside every working tree; the tool refuses to run without
it. Give the path with --rules, or set TRACEWEAVE_SCRUB_RULES, or set
TRACEWEAVE_EVAL_DIR (the rules are then read from
$TRACEWEAVE_EVAL_DIR/private/public-history-rules.json).

Commands:
  apply-tree [--categories a,b]  rewrite text files in the working tree
  scan [REV ...] [--tree]        scan every blob, path, commit message and author/
                                 committer header reachable from REV and not from
                                 --base, also after ROT13 and base64 decoding
  rewrite --branch NAME [--source REV] [--base REV] [--map-out FILE]
                                 replay --base..--source into a new branch
  map --branch NAME --idmap FILE --out FILE [--cite FILE ...]
                                 write the public-history map for the rewritten branch

Rewrite guarantees: commit order, authors, committer and author dates, parents
and file modes are kept; every text blob and message is rewritten with the same
rules; .json and .jsonl blobs are never rewritten (a match stops the run);
versions of this tool's own path whose blob id is listed in the private file
are dropped from every rewritten tree; a commit whose tree then equals its
parent's tree is dropped, and its id maps to its nearest surviving ancestor.

Rules file format (JSON): "rules" [category, scope, pattern, replacement],
"detectors" [category, exempt, pattern], "detector_only_paths" [category, scope,
pattern], "notes" [path, after_category, text], "categories" [name, description],
"allowed_emails", "drop_tool_blobs".
"""

from __future__ import annotations

import argparse
import base64
import binascii
import codecs
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

TOOL_PATH = "tools/public_history_scrub.py"
PROTECTED_SUFFIXES = (".json", ".jsonl")
EMAIL = re.compile(r"[A-Za-z0-9._+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
BASE64_TOKEN = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")


class Blocked(Exception):
    pass


class Rules:
    def __init__(self, path):
        raw = open(path, "rb").read()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        self.rules = [(r["category"], r.get("scope"), re.compile(r["pattern"]), r["replacement"]) for r in data["rules"]]
        self.detectors = [(d["category"], d.get("exempt"), re.compile(d["pattern"])) for d in data["detectors"]]
        self.detector_only = [(d["category"], d["scope"], re.compile(d["pattern"])) for d in data.get("detector_only_paths", [])]
        self.notes = data.get("notes", [])
        self.categories = data.get("categories", [])
        emails = data.get("allowed_emails", [])
        # An allowed address is also allowed in its ROT13 form, which is how it appears in the ROT13 decoding of the same text.
        self.allowed_emails = set(emails) | {codecs.decode(e, "rot13") for e in emails}
        self.drop_tool_blobs = set(data.get("drop_tool_blobs", []))


def rules_path(explicit):
    if explicit:
        return explicit
    if os.environ.get("TRACEWEAVE_SCRUB_RULES"):
        return os.environ["TRACEWEAVE_SCRUB_RULES"]
    if os.environ.get("TRACEWEAVE_EVAL_DIR"):
        return os.path.join(os.environ["TRACEWEAVE_EVAL_DIR"], "private", "public-history-rules.json")
    return None


def load_rules(explicit):
    path = rules_path(explicit)
    if not path or not os.path.exists(path):
        raise SystemExit("refusing to run: no rules file (use --rules, TRACEWEAVE_SCRUB_RULES or TRACEWEAVE_EVAL_DIR)")
    return Rules(path)


# ---------------------------------------------------------------------------- text
def scrub_text(rules, path, text, categories=None):
    counts = collections.Counter()
    for category, scope, pattern, replacement in rules.rules:
        if categories and category not in categories:
            continue
        if scope and (path is None or not re.search(scope, path)):
            continue
        text, n = pattern.subn(replacement, text)
        if n:
            counts[category] += n
    for note in rules.notes:
        if path == note["path"] and counts.get(note["after_category"]) and not text.startswith(note["text"]):
            text = note["text"] + text
    return text, counts


def scrub_blob(rules, path, data, categories=None):
    if b"\0" in data:
        return data, collections.Counter()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, collections.Counter()
    new, counts = scrub_text(rules, path, text, categories)
    if path.endswith(PROTECTED_SUFFIXES):
        if counts:
            raise Blocked(f"a substitution would change protected JSON bytes: {path} {dict(counts)}")
        return data, counts
    return new.encode("utf-8"), counts


def variants(text):
    """The text, its ROT13 decoding, and all printable base64 payloads found inside it (joined, and ROT13-decoded)."""
    yield "plain", text
    yield "rot13", codecs.decode(text, "rot13")
    payloads = []
    for token in set(BASE64_TOKEN.findall(text)):
        try:
            decoded = base64.b64decode(token + "=" * (-len(token) % 4), validate=True)
        except (binascii.Error, ValueError):
            continue
        try:
            payload = decoded.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if payload and sum(ch.isprintable() or ch in "\n\t" for ch in payload) / len(payload) > 0.95:
            payloads.append(payload)
    if payloads:
        joined = "\n".join(payloads)
        yield "base64", joined
        yield "base64+rot13", codecs.decode(joined, "rot13")


def residuals(rules, path, text):
    hits = collections.Counter()
    for _, candidate in variants(text):
        for category, exempt, pattern in rules.detectors:
            if exempt and path and re.search(exempt, path):
                continue
            for match in pattern.finditer(candidate):
                if EMAIL.fullmatch(match.group(0)) and match.group(0) in rules.allowed_emails:
                    continue
                hits[category] += 1
        if path:
            for category, scope, pattern in rules.detector_only:
                if re.search(scope, path):
                    n = len(pattern.findall(candidate))
                    if n:
                        hits[category] += n
    return hits


# ------------------------------------------------------------------------------ git
def git(*args, input=None, env=None):
    return subprocess.run(["git", *args], input=input, capture_output=True, check=True, env=env).stdout


def tracked_files():
    return [p for p in git("ls-files", "-z").decode().split("\0") if p]


def apply_tree(rules, categories):
    total = collections.Counter()
    for path in tracked_files():
        if path == TOOL_PATH:
            continue
        try:
            data = open(path, "rb").read()
        except OSError:
            continue
        new, counts = scrub_blob(rules, path, data, categories)
        if new != data:
            open(path, "wb").write(new)
            print("rewrote", path, dict(counts))
        total.update(counts)
    print("substitutions:", dict(total))


def scan_range(rules, revs, base):
    """Scan every object, path, message and commit header reachable from revs and not from base."""
    commits = git("rev-list", *revs, f"^{base}").decode().split()
    listing = git("rev-list", "--objects", *revs, f"^{base}").decode().splitlines()
    names = {}
    for line in listing:
        parts = line.split(" ", 1)
        names.setdefault(parts[0], parts[1] if len(parts) == 2 else "")
    kinds = ("blobs", "paths", "messages", "headers")
    hits = {k: collections.defaultdict(collections.Counter) for k in kinds}
    proc = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def read_object(oid):
        proc.stdin.write((oid + "\n").encode())
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        size = int(header[2])
        data = proc.stdout.read(size)
        proc.stdout.read(1)
        return header[1], data

    for oid, path in names.items():
        kind, data = read_object(oid)
        if path:
            for category, n in residuals(rules, None, path).items():
                hits["paths"][category][path] += n
        if kind != b"blob" or b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for category, n in residuals(rules, path, text).items():
            hits["blobs"][category][path] += n
    for commit in commits:
        kind, data = read_object(commit)
        head, _, message = data.decode("utf-8", "surrogateescape").partition("\n\n")
        for category, n in residuals(rules, None, head).items():
            hits["headers"][category][commit[:12]] += n
        for category, n in residuals(rules, None, message).items():
            hits["messages"][category][commit[:12]] += n
    proc.stdin.close()
    proc.wait()
    return len(commits), len(names), hits


def scan_tree(rules):
    hits = collections.defaultdict(collections.Counter)
    for path in tracked_files():
        try:
            text = open(path, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        for category, n in residuals(rules, path, text).items():
            hits[category][path] += n
    return hits


def categories_of(rules):
    seen = []
    for category, _, _ in rules.detectors:
        if category not in seen:
            seen.append(category)
    for category, _, _ in rules.detector_only:
        if category not in seen:
            seen.append(category)
    return seen


def run_scan(rules, args):
    if args.tree:
        hits = scan_tree(rules)
        total = 0
        for category in categories_of(rules):
            files = hits.get(category, {})
            print(f"{category}: {sum(files.values())} hits")
            for path, n in sorted(files.items())[:20]:
                print("   ", path, n)
            total += sum(files.values())
        return 1 if total else 0
    n_commits, n_objects, hits = scan_range(rules, args.revs or ["HEAD"], args.base)
    print(f"scanned {n_commits} commits and {n_objects} objects not reachable from {args.base} (plain, ROT13 and base64 decodings)")
    total = 0
    for category in categories_of(rules):
        per = {kind: sum(hits[kind].get(category, {}).values()) for kind in hits}
        n = sum(per.values())
        total += n
        print(f"{category}: {n} hits ({', '.join(f'{k}: {v}' for k, v in per.items())})")
        for kind in hits:
            for where, count in sorted(hits[kind].get(category, {}).items())[:10]:
                print("   ", kind, where, count)
    return 1 if total else 0


# --------------------------------------------------------------------------- rewrite
def rewrite(rules, args):
    commits = git("rev-list", "--reverse", "--topo-order", args.source, f"^{args.base}").decode().split()
    counts = collections.Counter()
    blob_cache = {}
    idmap = {}
    dropped = []
    dropped_tool = collections.OrderedDict()

    def new_blob(oid, path):
        key = (oid, path)
        if key not in blob_cache:
            data = git("cat-file", "blob", oid)
            new, c = scrub_blob(rules, path, data)
            counts.update(c)
            blob_cache[key] = oid if new == data else git("hash-object", "-w", "--stdin", input=new).decode().strip()
        return blob_cache[key]

    for c in commits:
        raw = git("cat-file", "commit", c)
        head, _, message = raw.partition(b"\n\n")
        meta, parents = {}, []
        for line in head.decode("utf-8", "surrogateescape").split("\n"):
            key, _, value = line.partition(" ")
            if key == "parent":
                parents.append(idmap.get(value, value))
            elif key in ("author", "committer"):
                meta[key] = value
            elif key in ("encoding", "gpgsig") or line.startswith(" "):
                raise SystemExit(f"unsupported commit header in {c}: {key}")
        lines = []
        for entry in git("ls-tree", "-r", "-z", c).decode("utf-8", "surrogateescape").split("\0"):
            if not entry:
                continue
            info, path = entry.split("\t", 1)
            mode, kind, oid = info.split()
            if kind == "blob":
                if path == TOOL_PATH and oid in rules.drop_tool_blobs:
                    dropped_tool.setdefault(oid, []).append(c)
                    continue
                oid = new_blob(oid, path)
            lines.append(f"{mode} {oid}\t{path}")
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, GIT_INDEX_FILE=os.path.join(directory, "index"))
            subprocess.run(["git", "update-index", "--index-info"], input=("\n".join(lines) + "\n").encode("utf-8", "surrogateescape"), env=env, check=True)
            tree = subprocess.run(["git", "write-tree"], env=env, capture_output=True, check=True).stdout.decode().strip()
        if parents and git("rev-parse", f"{parents[0]}^{{tree}}").decode().strip() == tree:
            idmap[c] = parents[0]
            dropped.append((c, parents[0], git("log", "-1", "--format=%s", c).decode().strip()))
            continue
        message_text, message_counts = scrub_text(rules, None, message.decode("utf-8", "surrogateescape"))
        counts.update(message_counts)

        def ident(value):
            name_email, _, date = value.rpartition("> ")
            name, _, email = name_email.partition(" <")
            return name, email, date

        an, ae, ad = ident(meta["author"])
        cn, ce, cd = ident(meta["committer"])
        env = dict(os.environ, GIT_AUTHOR_NAME=an, GIT_AUTHOR_EMAIL=ae, GIT_AUTHOR_DATE=ad,
                   GIT_COMMITTER_NAME=cn, GIT_COMMITTER_EMAIL=ce, GIT_COMMITTER_DATE=cd)
        command = ["git", "commit-tree", tree]
        for parent in parents:
            command += ["-p", parent]
        idmap[c] = subprocess.run(command, input=message_text.encode("utf-8", "surrogateescape"), env=env,
                                  capture_output=True, check=True).stdout.decode().strip()
    git("update-ref", f"refs/heads/{args.branch}", idmap[commits[-1]])
    return counts, idmap, commits, dropped, dropped_tool


def write_idmap(path, idmap, commits, dropped):
    dropped_ids = {d[0] for d in dropped}
    with open(path, "w") as handle:
        for old in commits:
            handle.write(f"{old}\t{idmap[old]}\t{'dropped' if old in dropped_ids else 'kept'}\n")


# ------------------------------------------------------------------------------ map
def cited_commits(cite_files, idmap):
    found = collections.OrderedDict()
    text = "".join(open(f, encoding="utf-8").read() for f in cite_files)
    for match in re.finditer(r"\b[0-9a-f]{7,40}\b", text):
        hits = [c for c in idmap if c.startswith(match.group(0))]
        if len(hits) == 1:
            found[match.group(0)] = hits[0]
    return found


def write_map(rules, args):
    rows = [line.split("\t") for line in open(args.idmap).read().splitlines() if line]
    idmap = {o: n for o, n, _ in rows}
    status = {o: s for o, _, s in rows}
    commits = [o for o, _, _ in rows]
    counts = json.loads(open(args.counts).read()) if args.counts else {}
    n_commits, n_objects, hits = scan_range(rules, [args.branch], args.base)
    category_hits = collections.OrderedDict()
    for category in categories_of(rules):
        category_hits[category] = sum(sum(hits[kind].get(category, {}).values()) for kind in hits)

    def ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b]).returncode == 0

    items = list(cited_commits(args.cite, idmap).items())
    pairs = mismatches = 0
    for i, (_, o1) in enumerate(items):
        for _, o2 in items[i + 1:]:
            pairs += 1
            for x, y in ((o1, o2), (o2, o1)):
                if ancestor(x, y) != ancestor(idmap[x], idmap[y]):
                    mismatches += 1
    L = ["# Public history map", ""]
    L.append(f"This history was produced from the local branch `{args.source_name}` so that it can be published. The local branch keeps its original history, and the reviews and gate records in this repository cite its commit ids. Every commit between `origin/main` and the source tip was recreated with the same order, authors, author and committer dates, parents (mapped) and file modes. Only text content changed, by the fixed substitutions below, and the rewrite tool's own earlier versions were dropped (see below).")
    L.append("")
    L.append("**The text of this repository, including its reviews and gate records, cites the old commit ids.** They do not exist in this history. Use the table below to translate an old id to the new id.")
    L.append("")
    L.append("**Scope of this map.** It is a file in the source history, so it can only list the commits that come before the commit that adds it; that commit and later ones are not listed, and their new ids follow from rerunning the rewrite. The rewrite is append-stable: new source commits never change the ids of earlier public commits, so each published tip is an ancestor of the next one. Regenerating the map is a new source commit, and the map is not an input to the ids it lists.")
    L.append("")
    L.append("## Reproducing")
    L.append("")
    L.append(f"`python3 tools/public_history_scrub.py rewrite --branch NAME --source <source commit>` with the private rules file. The rules are not in this repository in any form. Rules file SHA-256: `{rules.sha256}`.")
    L.append("")
    L.append("## What was substituted, by category")
    L.append("")
    L.append("The same fixed rules were applied to every text blob in every commit and to every commit message. The removed strings are not reproduced here. Counts are substitutions made, each counted once per distinct file version (and once per commit message).")
    L.append("")
    L.append("| Category | What was replaced | Substitutions |")
    L.append("| --- | --- | --- |")
    for c in rules.categories:
        L.append(f"| {c['name']} | {c['description']} | {counts.get(c['name'], 0)} |")
    L.append("")
    L.append("Unchanged on purpose: the git author identity (already public on `origin/main`), the GitHub repository URL, public third-party names, and every `.json` and `.jsonl` file (vectors, configurations, schemas, results, manifests). A substitution that would touch one of those files stops the rewrite; none did.")
    L.append("")
    L.append("## Dropped file versions and commits")
    L.append("")
    L.append(f"Every version of `{TOOL_PATH}` that held the rules was removed from every rewritten tree: {args.dropped_versions} versions. A commit whose tree became equal to its parent's tree was dropped, and its old id maps to the id of its nearest surviving ancestor (listed below as `dropped`).")
    L.append("")
    L.append("## Verification of the commits listed here")
    L.append("")
    L.append(f"`python3 tools/public_history_scrub.py scan` over the {n_commits} commits and {n_objects} objects of the rewritten history before the map commit, in plain text, ROT13 and base64 decodings, over blobs, paths, messages and author and committer headers:")
    L.append("")
    L.append("| Category | Hits |")
    L.append("| --- | --- |")
    for category, n in category_hits.items():
        L.append(f"| {category} | {n} |")
    L.append("")
    L.append("## Commit ids cited by the roadmap and the work queue")
    L.append("")
    L.append("| Cited as | Old id | New id |")
    L.append("| --- | --- | --- |")
    for short, old in items:
        L.append(f"| `{short}` | `{old[:12]}` | `{idmap[old][:12]}` |")
    L.append("")
    L.append(f"Ancestry was checked for all {pairs} pairs of these {len(items)} ids in both directions: the relation is the same before and after the rewrite ({mismatches} mismatches).")
    L.append("")
    L.append("## All commits, oldest first")
    L.append("")
    L.append("| # | Old id | New id | State | Subject |")
    L.append("| --- | --- | --- | --- | --- |")
    for i, old in enumerate(commits, 1):
        subject = git("log", "-1", "--format=%s", old).decode().strip().replace("|", "/")
        L.append(f"| {i} | `{old[:12]}` | `{idmap[old][:12]}` | {status[old]} | {subject} |")
    open(args.out, "w").write("\n".join(L) + "\n")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rules", help="path of the private rules file")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply-tree")
    a.add_argument("--categories", default="")
    s = sub.add_parser("scan")
    s.add_argument("revs", nargs="*")
    s.add_argument("--base", default="origin/main")
    s.add_argument("--tree", action="store_true")
    r = sub.add_parser("rewrite")
    r.add_argument("--branch", required=True)
    r.add_argument("--base", default="origin/main")
    r.add_argument("--source", default="HEAD")
    r.add_argument("--map-out")
    r.add_argument("--counts-out")
    m = sub.add_parser("map")
    m.add_argument("--branch", required=True)
    m.add_argument("--base", default="origin/main")
    m.add_argument("--idmap", required=True)
    m.add_argument("--counts")
    m.add_argument("--out", required=True)
    m.add_argument("--cite", nargs="*", default=[])
    m.add_argument("--source-name", default="roadmap-v2")
    m.add_argument("--dropped-versions", default="0")
    args = parser.parse_args(argv)
    rules = load_rules(args.rules)
    if args.cmd == "apply-tree":
        apply_tree(rules, {c for c in args.categories.split(",") if c} or None)
        return 0
    if args.cmd == "scan":
        return run_scan(rules, args)
    if args.cmd == "map":
        return write_map(rules, args)
    counts, idmap, commits, dropped, dropped_tool = rewrite(rules, args)
    if args.map_out:
        write_idmap(args.map_out, idmap, commits, dropped)
    if args.counts_out:
        json.dump(dict(counts), open(args.counts_out, "w"))
    print("substitutions by category:", dict(counts))
    print(f"commits: {len(commits)} source, {len(commits) - len(dropped)} kept, {len(dropped)} dropped; tool versions dropped: {len(dropped_tool)}")
    for old, mapped, subject in dropped:
        print(f"dropped {old[:12]} -> {mapped[:12]}: {subject}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
