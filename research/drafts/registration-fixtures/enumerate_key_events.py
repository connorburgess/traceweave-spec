#!/usr/bin/env python3
"""Adversarial enumeration of the key-event state machine (design draft-4, section 8).

Standard library only. It enumerates every event sequence of length 1 to MAX_LEN over
  {rotate, retire, compromise} x {signed by current, old, successor, attacker key}
  x {earlier, equal, later proved time than the previous event}
and checks invariants on the outcomes of the checker's own `evaluate_events` and `signer_trust`.
The events are given to those functions as the dictionaries `load_events` produces; the
signatures and time evidence behind them are tested by the fixtures, not here.

Model. Keys: K (the trusted original), S and S2 (the honest successors), A (an attacker).
  - "current": the honest owner, using the honest chain's current key at that point
    (K, then S after an honest rotation, then S2); rotate goes to the next honest key.
  - "old": whoever holds a copy of K; rotate goes to A (a thief); compromise or retire K.
  - "successor": the holder of S, acting on K (retire or compromise K), or rotating S to S2.
  - "attacker": A, acting on K; never authorized.
  Proved times step by +-40 days ("earlier", "later") or 0 ("equal"), so a step crosses the 30-day
  look-back. A compromise claims a start 60 days before its proved time.

Invariants (each failure prints the sequence):
  I1 order: reversing the input order gives identical outcomes and trust.
  I2 attacker: removing every event signed by A changes nothing (except their own entries).
  I3 supersession: an event signed by a key after that key's first applied rotation or retirement,
     other than `compromised`, is never applied or disputed.
  I4 retired keys: a key is never trusted for a bound at or after any applied or disputed rotation or
     retirement of it, nor at or after the start of an applied compromise of it.
  I5 chain: a successor is trusted only through an applied, undisputed rotation from a key that is
     itself trusted at that rotation's proved time.
  I6 honest chain: once the owner has rotated K to S, events signed with K later than the look-back
     window after that rotation never change any outcome for S or S2.
  I7 thief window: A is trusted only if its rotation from K was K's first supersession and no
     applied compromise of K starts at or before it.

Usage: python3 -I enumerate_key_events.py [max_len]   (default 4; exit status 1 on any violation)
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_registration", HERE / "check_registration.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)

K, S, S2, A = (hashlib.sha256(f"enumeration key {n}".encode()).hexdigest() for n in ("K", "S", "S2", "A"))
NAMES = {K: "K", S: "S", S2: "S2", A: "A"}
NEXT_HONEST = {K: S, S: S2, S2: None}
T0 = datetime(2027, 1, 1, tzinfo=timezone.utc)
STEP = {"earlier": timedelta(days=-40), "equal": timedelta(0), "later": timedelta(days=40)}
LOOKBACK = timedelta(days=30)
POLICY = {"trustedKeys": [K], "compromiseLookbackSeconds": int(LOOKBACK.total_seconds())}
EVENTS = ("rotate", "retire", "compromise")
ROLES = ("current", "old", "successor", "attacker")
TIMES = ("earlier", "equal", "later")


def build(seq):
    """Turn a sequence of (event, role, time) into event dictionaries, tracking the honest current key."""
    out, current, e_prev = [], K, T0
    for i, (kind, role, when) in enumerate(seq):
        e_time = e_prev + STEP[when] if i else T0 + STEP[when]
        e_prev = e_time
        succ = None
        if role == "current":
            signer = target = current
            if kind == "rotate":
                succ = NEXT_HONEST[current]
                if succ is None:
                    kind = "retire"
        elif role == "old":
            signer = target = K
            succ = A if kind == "rotate" else None
        elif role == "successor":
            signer = S
            target = S if kind == "rotate" else K
            succ = S2 if kind == "rotate" else None
        else:
            signer, target = A, K
            succ = A if kind == "rotate" else None
        event = {"rotate": "rotated", "retire": "retired", "compromise": "compromised"}[kind]
        if role == "current" and event == "rotated":
            current = succ
        out.append({"hash": hashlib.sha256(f"{i}|{kind}|{role}|{when}".encode()).hexdigest(), "file": "",
                    "target": target, "signer": signer, "event": event, "E": e_time, "sigok": True,
                    "claimed": e_time - timedelta(days=60) if event == "compromised" else None,
                    "successor": succ, "role": role})
    return out


def evaluate(evs):
    results, ok, applied = C.evaluate_events(evs, POLICY)
    bound_time = max(e["E"] for e in evs) + timedelta(days=1)
    trust = {}
    for key in (K, S, S2, A):
        for probe in (bound_time, T0 - timedelta(days=400)):
            trust[(key, probe == bound_time)] = C.signer_trust(key, "valid", {"quorum": probe, "anyRoot": probe}, POLICY, ok, applied)
    return {r["eventSha256"]: r["outcome"] for r in results}, trust, ok, applied, bound_time


def describe(seq):
    return " ; ".join(f"{k}/{r}/{t}" for k, r, t in seq)


def check(seq):
    evs = build(seq)
    outcomes, trust, ok, applied, bound = evaluate(evs)
    problems = []
    # I1 order independence
    o2, t2, *_ = evaluate(list(reversed(evs)))
    if (o2, t2) != (outcomes, trust):
        problems.append("I1 order")
    # I2 attacker events change nothing
    rest = [e for e in evs if e["signer"] != A]
    if rest:
        o3, t3, *_ = evaluate(rest)
        if t3 != trust or any(o3[h] != outcomes[h] for h in o3):
            problems.append("I2 attacker")
    # I3 supersession
    first_sup = {}
    for e in sorted(applied, key=lambda e: (e["E"], e["hash"])):
        if e["event"] in ("rotated", "retired"):
            first_sup.setdefault(e["target"], e["E"])
    for e in evs:
        t = first_sup.get(e["signer"])
        if t is not None and e["event"] != "compromised" and e["E"] > t and outcomes[e["hash"]] in ("applied", "disputed"):
            problems.append("I3 supersession")
    # I4 retired, rotated-away or compromised keys
    for key in (K, S, S2, A):
        if trust[(key, True)] != "trusted":
            continue
        for e in applied:
            if e["target"] != key:
                continue
            if e["event"] in ("rotated", "retired") and e["E"] <= bound:
                problems.append(f"I4 {NAMES[key]} trusted after its supersession")
            if e["event"] == "compromised" and max(e["claimed"], e["E"] - LOOKBACK) <= bound:
                problems.append(f"I4 {NAMES[key]} trusted after a compromise start")
    # I5 chain
    for key in (S, S2, A):
        if trust[(key, True)] == "trusted":
            via = [r for r in ok if r["event"] == "rotated" and r["successor"] == key and r["E"] <= bound]
            if not any(C.signer_trust(r["target"], "valid", {"quorum": r["E"] - timedelta(seconds=1), "anyRoot": None},
                                      POLICY, ok, applied) == "trusted" or r["target"] == K for r in via):
                problems.append(f"I5 {NAMES[key]} trusted without a trusted rotation")
    # I6 honest chain not erased by much later events signed with K
    honest = [e for e in evs if e["role"] == "current" and e["event"] == "rotated" and e["target"] == K]
    if honest:
        e_r = min(e["E"] for e in honest)
        later = [e for e in evs if e["signer"] == K and e["role"] == "old" and e["E"] > e_r + LOOKBACK]
        if later:
            kept = [e for e in evs if e not in later]
            o4, t4, *_ = evaluate(kept)
            for key in (S, S2):
                if t4[(key, True)] != trust[(key, True)]:
                    problems.append(f"I6 honest chain changed for {NAMES[key]}")
    # I7 thief window
    if trust[(A, True)] == "trusted":
        rot = [r for r in ok if r["successor"] == A]
        if not rot or any(e["E"] < rot[0]["E"] for e in applied if e["target"] == K and e["event"] in ("rotated", "retired") and e is not rot[0]):
            problems.append("I7 thief trusted although K was already superseded")
    return problems


def naive_evaluate(evs, policy):
    """Weakened rules for the mutation check: every self-signed event applies; nothing supersedes or disputes."""
    order = sorted(evs, key=lambda e: (e["E"], e["hash"]))
    applied = [e for e in order if e["signer"] == e["target"]]
    results = [{"eventSha256": e["hash"], "keySha256": e["target"], "event": e["event"],
                "outcome": "applied" if e in applied else "ignored-unauthorized", "provedAt": C.fmt_time(e["E"])} for e in order]
    return results, applied, applied


def mutation_check():
    """The invariants must catch weakened rules, so the enumeration is not vacuous."""
    real_eval, real_trust = C.evaluate_events, C.signer_trust
    alphabet = list(itertools.product(EVENTS, ROLES, TIMES))
    found = {}
    variants = {
        "no supersession or disputes (draft-2 style)": (naive_evaluate, real_trust),
        "trust flows through disputed rotations": (real_eval, lambda d, o, b, p, ok, ap: real_trust(d, o, b, p, ap, ap)),
    }
    try:
        for name, (ev, tr) in variants.items():
            C.evaluate_events, C.signer_trust = ev, tr
            found[name] = sum(1 for n in (1, 2, 3) for seq in itertools.product(alphabet, repeat=n) if check(seq))
    finally:
        C.evaluate_events, C.signer_trust = real_eval, real_trust
    for name, count in found.items():
        print(f"mutation check, {name}: {count} sequences with violations (must be > 0)")
    return all(found.values())


def main(argv):
    max_len = int(argv[0]) if argv else 4
    if not mutation_check():
        print("FAIL: the invariants did not catch a weakened rule set")
        return 1
    alphabet = list(itertools.product(EVENTS, ROLES, TIMES))
    started = time.time()
    checked = violations = 0
    for n in range(1, max_len + 1):
        for seq in itertools.product(alphabet, repeat=n):
            problems = check(seq)
            checked += 1
            if problems:
                violations += 1
                if violations <= 20:
                    print("VIOLATION", sorted(set(problems)), "::", describe(seq))
    print(f"{checked} sequences of length 1-{max_len} over {len(alphabet)} events; {violations} with violations; "
          f"{time.time() - started:.0f} s")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
