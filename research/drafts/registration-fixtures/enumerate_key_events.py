#!/usr/bin/env python3
"""Adversarial enumeration of the key-event state machine (design draft-5, section 8).

Standard library only. Two parts:

1. Dictionary enumeration. Every event sequence of length 1 to 3 over the alphabet
     {rotate, retire} x {current, old, successor, attacker} x 5 time steps            (40 symbols)
   + {compromise}      x {current, old, successor, attacker} x 5 time steps x 3 claimed starts (60)
   = 100 symbols, 1,010,100 sequences; plus a seeded random sample of length-4 sequences.
   Time steps from the previous event: -40 d, -10 d, 0, +10 d, +40 d, so steps are both shorter and
   longer than the 30-day look-back. A compromise claims a start 2, 20 or 60 days before its proved time.
   Events go to the checker's own `evaluate_events` and `signer_trust` as the dictionaries that
   `load_event_bundles` produces.

2. Loading sample. A seeded sample of sequences is rebuilt as real signed key-event bundles with the
   builder (Ed25519 signatures, subject digests, keyid hints, placeholder time evidence), with some
   events tampered (bad signature), left without a proved time (one source only), or given a subject
   that disagrees with the keyid. They are loaded through `load_event_bundles`, and the outcomes must
   equal the dictionary path's.

Model. Keys: K (the trusted original), S and S2 (honest successors), A (attacker).
  "current": the honest owner, with the honest chain's current key (K, then S, then S2); rotate goes to
  the next honest key. "old": whoever holds a copy of K; rotate goes to A. "successor": the holder of S,
  acting on K (retire, compromise) or rotating S to S2. "attacker": A acting on K; never authorized.

Probes: every key at the final time + 1 d, at T0 - 400 d, at E - 1 s and E of every event, and at
start - 1 s and start of every compromise window; plus a no-quorum probe per key.

Invariants:
  I1  order: reversing the input gives identical outcomes and trust.
  I2  removing every rejected event (ignored-unauthorized or ignored-superseded) changes nothing else.
      (An attacker key can gain standing legitimately once the old key rotates to it, so "attacker-signed"
      is not the right class; the draft-4 invariant of that name was wrong.)
  I3  supersession: after a key's first applied rotation or retirement, no event it signs other than a
      compromise report is applied or disputed.
  I4  no key is trusted at or after its own applied (or disputed) rotation or retirement, or at or after
      the start of an applied compromise of it.
  I5  chain: a successor is trusted only through an undisputed rotation from a key trusted just before it.
  I6  honest chain final: events about K proved later than the look-back window after the owner's
      rotation K->S, whoever signs them (old key or successor), never change S's or S2's trust.
  I7  thief window: A is trusted only if its rotation was K's first supersession and undisputed.
  I8  compromise window: inside [start, E) of an applied compromise of X, X is never trusted; just below
      the start, X's trust is the same as without that report.
  I9  no quorum: a key touched by any applied event is never trusted for a bound without quorum.
  I10 rejected events: adding an event signed by a key with no standing (J), at the middle or final
      proved time, as a retirement, compromise report or rotation, changes nothing else.
  I11 who may sign: every applied event is signed by its target, or by the successor of an applied
      rotation of that target with a smaller proved time.
  I12 equal times: two different applied supersessions of one key at the same proved time are both disputed.
  I13 own standing: a compromise report never disputes the rotation that gives its own signer standing.

Mutation check: the same invariants on length <= 2 (and 3 for the cheap variants) against weakened rule
sets must find violations: no supersession; trust through disputed rotations; and the draft-4 fixed-point
rule (reports may dispute their own appointment, with a pass limit).

Usage: python3 -I enumerate_key_events.py [--quick]   (exit status 1 on any violation)
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import multiprocessing
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _load("check_registration", HERE / "check_registration.py")

K, S, S2, A, J = (hashlib.sha256(f"enumeration key {n}".encode()).hexdigest() for n in ("K", "S", "S2", "A", "J"))
NAMES = {K: "K", S: "S", S2: "S2", A: "A", J: "J"}
NEXT_HONEST = {K: S, S: S2, S2: None}
T0 = datetime(2027, 1, 1, tzinfo=timezone.utc)
STEPS = {"-40d": -40, "-10d": -10, "0": 0, "+10d": 10, "+40d": 40}
CLAIMS = (2, 20, 60)
LOOKBACK = timedelta(days=30)
POLICY = {"trustedKeys": [K], "recoveryKeys": [], "compromiseLookbackSeconds": int(LOOKBACK.total_seconds())}
ROLES = ("current", "old", "successor", "attacker")
ALPHABET = ([(k, r, t, None) for k in ("rotate", "retire") for r in ROLES for t in STEPS]
            + [("compromise", r, t, c) for r in ROLES for t in STEPS for c in CLAIMS])
SEC = timedelta(seconds=1)


def build(seq):
    """(kind, role, step, claim) tuples -> event dictionaries, tracking the honest current key."""
    out, current, e_prev = [], K, T0
    for i, (kind, role, step, claim) in enumerate(seq):
        e_time = (e_prev if i else T0) + timedelta(days=STEPS[step])
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
        out.append({"hash": hashlib.sha256(f"{i}|{kind}|{role}|{step}|{claim}".encode()).hexdigest(), "file": "",
                    "target": target, "signer": signer, "event": event, "E": e_time, "sigok": True,
                    "claimed": e_time - timedelta(days=claim) if event == "compromised" else None,
                    "successor": succ, "role": role})
    return out


def probes(evs):
    ts = {T0 - timedelta(days=400), max(e["E"] for e in evs) + timedelta(days=1)}
    for e in evs:
        ts |= {e["E"] - SEC, e["E"]}
        if e["event"] == "compromised":
            st = max(e["claimed"], e["E"] - LOOKBACK)
            ts |= {st - SEC, st}
    return sorted(ts)


def evaluate(evs, times=None):
    results, ok, applied = C.evaluate_events(evs, POLICY)
    times = times or probes(evs)
    trust = {}
    for key in (K, S, S2, A):
        for t in times:
            trust[(key, t)] = C.signer_trust(key, "valid", {"quorum": t, "anyRoot": t}, POLICY, ok, applied)
        trust[(key, "no-quorum")] = C.signer_trust(key, "valid", {"quorum": None, "anyRoot": times[-1]}, POLICY, ok, applied)
    return {r["eventSha256"]: r["outcome"] for r in results}, trust, ok, applied, times


def start_of(c):
    return max(c["claimed"], c["E"] - LOOKBACK)


def check(seq):
    evs = build(seq)
    outcomes, trust, ok, applied, times = evaluate(evs)
    final = times[-1]
    problems = []
    disputed = {h for h, o in outcomes.items() if o == "disputed"}
    applied_h = {e["hash"] for e in applied}

    def same_for(subset_outcomes, subset_trust, keep):
        return subset_trust == trust and all(subset_outcomes[h] == outcomes[h] for h in keep)

    # I1
    o2, t2, *_ = evaluate(list(reversed(evs)), times)
    if (o2, t2) != (outcomes, trust):
        problems.append("I1 order")
    # I2
    rest = [e for e in evs if outcomes[e["hash"]] not in ("ignored-unauthorized", "ignored-superseded")]
    if rest and len(rest) < len(evs):
        o3, t3, *_ = evaluate(rest, times)
        if not same_for(o3, t3, o3):
            problems.append("I2 rejected events removed")
    # I3
    first_sup = {}
    for e in sorted(applied, key=lambda e: (e["E"], e["hash"])):
        if e["event"] in ("rotated", "retired"):
            first_sup.setdefault(e["target"], e["E"])
    for e in evs:
        t = first_sup.get(e["signer"])
        if t is not None and e["event"] != "compromised" and e["E"] > t and outcomes[e["hash"]] in ("applied", "disputed"):
            problems.append("I3 supersession")
    # I4
    for (key, t), v in trust.items():
        if v != "trusted" or t == "no-quorum":
            continue
        for e in applied:
            if e["target"] == key and e["event"] in ("rotated", "retired") and e["E"] <= t:
                problems.append(f"I4 {NAMES[key]} trusted after its supersession")
            if e["target"] == key and e["event"] == "compromised" and start_of(e) <= t:
                problems.append(f"I4 {NAMES[key]} trusted after a compromise start")
    # I5
    for (key, t), v in trust.items():
        if v == "trusted" and key != K and t != "no-quorum":
            via = [r for r in ok if r["event"] == "rotated" and r["successor"] == key and r["E"] <= t]
            if not any(r["target"] == K or C.signer_trust(r["target"], "valid", {"quorum": r["E"] - SEC, "anyRoot": None},
                                                          POLICY, ok, applied) == "trusted" for r in via):
                problems.append(f"I5 {NAMES[key]} trusted without a trusted rotation")
    # I6
    honest = [e for e in evs if e["role"] == "current" and e["event"] == "rotated" and e["target"] == K]
    if honest:
        e_r = min(e["E"] for e in honest)
        late = [e for e in evs if e["target"] == K and e["role"] in ("old", "successor") and e["E"] > e_r + LOOKBACK]
        if late:
            kept = [e for e in evs if e not in late]
            _, t4, *_ = evaluate(kept, times)
            if any(t4[(k, final)] != trust[(k, final)] for k in (S, S2)):
                problems.append("I6 honest chain changed by a late event")
    # I7
    for t in times:
        if trust[(A, t)] == "trusted":
            rot = [r for r in ok if r["successor"] == A]
            if not rot or any(e["E"] < rot[0]["E"] for e in applied if e["target"] == K and e["event"] in ("rotated", "retired") and e is not rot[0]):
                problems.append("I7 thief trusted outside the theft window")
    # I8
    for c in applied:
        if c["event"] != "compromised":
            continue
        st = start_of(c)
        for t in times:
            if st <= t < c["E"] and trust[(c["target"], t)] == "trusted":
                problems.append(f"I8 {NAMES[c['target']]} trusted inside a compromise window")
        without = [e for e in evs if e is not c]
        _, t5, *_ = evaluate(without, [st - SEC])
        if t5[(c["target"], st - SEC)] != C.signer_trust(c["target"], "valid", {"quorum": st - SEC, "anyRoot": st - SEC}, POLICY, ok, applied):
            problems.append(f"I8 {NAMES[c['target']]} changed below the window start")
    # I9
    for key in (K, S, S2, A):
        touched = any(e["target"] == key or e["successor"] == key for e in applied)
        if touched and trust[(key, "no-quorum")] == "trusted":
            problems.append(f"I9 {NAMES[key]} trusted without quorum")
    # I10
    for when in (evs[len(evs) // 2]["E"], final):
        for ev in ("retired", "compromised", "rotated"):
            junk = {"hash": hashlib.sha256(f"junk|{when}|{ev}".encode()).hexdigest(), "file": "", "target": K, "signer": J,
                    "event": ev, "E": when, "sigok": True, "claimed": when - timedelta(days=60) if ev == "compromised" else None,
                    "successor": A if ev == "rotated" else None, "role": "attacker"}
            o6, t6, *_ = evaluate(evs + [junk], times)
            if not same_for(o6, t6, outcomes):
                problems.append("I10 a rejected event changed the result")
    # I11
    for e in applied:
        if e["signer"] != e["target"] and not any(r["event"] == "rotated" and r["target"] == e["target"] and r["successor"] == e["signer"]
                                                  and r["E"] < e["E"] and r["hash"] in applied_h for r in applied):
            problems.append("I11 applied event without standing")
    # I12
    groups = {}
    for e in applied:
        if e["event"] in ("rotated", "retired"):
            groups.setdefault((e["target"], e["E"]), []).append(e)
    for g in groups.values():
        if len({(e["event"], e["successor"]) for e in g}) > 1 and any(e["hash"] not in disputed for e in g):
            problems.append("I12 equal-time supersessions not both disputed")
    # I13
    for c in applied:
        if c["event"] == "compromised" and c["signer"] != c["target"]:
            own = [r for r in applied if r["event"] == "rotated" and r["target"] == c["target"] and r["successor"] == c["signer"] and r["E"] < c["E"]]
            if own and own[0]["hash"] in disputed and not any(
                    o["event"] in ("rotated", "retired") and o["target"] == c["target"] and o["E"] == own[0]["E"] and o is not own[0] for o in applied) \
                    and not any(x["event"] == "compromised" and x is not c and x["target"] == c["target"] and start_of(x) <= own[0]["E"]
                                and x["signer"] != c["signer"] for x in applied):
                problems.append("I13 a report disputed its own appointment")
    return problems


# ------------------------------------------------------------------ mutation check

def naive_evaluate(evs, policy):
    order = sorted(evs, key=lambda e: (e["E"], e["hash"]))
    applied = [e for e in order if e["signer"] == e["target"]]
    results = [{"eventSha256": e["hash"], "keySha256": e["target"], "event": e["event"],
                "outcome": "applied" if e in applied else "ignored-unauthorized", "provedAt": C.fmt_time(e["E"])} for e in order]
    return results, applied, applied


def draft4_evaluate(evs, policy):
    """The draft-4 rule: standing requires an undisputed rotation, iterated to a fixed point with a pass limit."""
    lookback = timedelta(seconds=policy["compromiseLookbackSeconds"])
    order = sorted(evs, key=lambda e: (e["E"], e["hash"]))
    disputed, state, applied, status = set(), None, [], {}
    for _ in range(len(order) + 2):
        applied, status, superseded = [], {}, {}
        for e in order:
            if not (e["signer"] == e["target"] or any(r["event"] == "rotated" and r["target"] == e["target"] and r["successor"] == e["signer"]
                                                      and r["E"] < e["E"] and r["hash"] not in disputed for r in applied)):
                status[e["hash"]] = "ignored-unauthorized"
                continue
            sup = e["event"] in ("rotated", "retired")
            bs = superseded.get(e["signer"])
            if bs is not None and e["event"] != "compromised" and not (sup and e["target"] == e["signer"] and e["E"] == bs):
                status[e["hash"]] = "ignored-superseded"
                continue
            bt = superseded.get(e["target"])
            if sup and bt is not None and e["E"] > bt:
                status[e["hash"]] = "ignored-superseded"
                continue
            applied.append(e)
            status[e["hash"]] = "applied"
            if sup and e["target"] not in superseded:
                superseded[e["target"]] = e["E"]
        new = set()
        ties = {}
        for e in applied:
            if e["event"] in ("rotated", "retired"):
                ties.setdefault((e["target"], e["E"]), set()).add((e["event"], e["successor"], e["hash"]))
        for g in ties.values():
            if len({(a, b) for a, b, _ in g}) > 1:
                new |= {h for _, _, h in g}
        for c in applied:
            if c["event"] == "compromised":
                st = max(c["claimed"], c["E"] - lookback)
                for r in applied:
                    if r is not c and r["target"] == c["target"] and r["event"] in ("rotated", "retired") and r["E"] >= st:
                        new.add(r["hash"])
        key = (tuple(e["hash"] for e in applied), frozenset(new))
        if key == state:
            break
        state, disputed = key, new
    results = [{"eventSha256": e["hash"], "keySha256": e["target"], "event": e["event"],
                "outcome": "disputed" if e["hash"] in disputed else status.get(e["hash"], "ignored-unauthorized"),
                "provedAt": C.fmt_time(e["E"])} for e in order]
    return results, [e for e in applied if e["hash"] not in disputed], applied


def mutation_check(lengths):
    real_eval, real_trust = C.evaluate_events, C.signer_trust
    variants = {
        "no supersession or disputes": (naive_evaluate, real_trust),
        "trust through disputed rotations": (real_eval, lambda d, o, b, p, ok, ap: real_trust(d, o, b, p, ap, ap)),
        "draft-4 fixed point (reports may dispute their own appointment)": (draft4_evaluate, real_trust),
    }
    found = {}
    try:
        for name, (ev, tr) in variants.items():
            C.evaluate_events, C.signer_trust = ev, tr
            found[name] = sum(1 for n in lengths for seq in itertools.product(ALPHABET, repeat=n) if check(seq))
    finally:
        C.evaluate_events, C.signer_trust = real_eval, real_trust
    for name, count in found.items():
        print(f"mutation check, {name}: {count} sequences with violations at length <= {max(lengths)} (must be > 0)")
    return all(found.values())


# ------------------------------------------------------------------ loading sample

def loading_sample(n, seed=20261124):
    B = _load("build_fixtures", HERE / "build_fixtures.py")
    keys = {K: B.CREATOR, S: B.NEXT, S2: B.CO, A: B.THIEF}
    rng = random.Random(seed)
    mismatches = 0
    for _ in range(n):
        seq = [rng.choice(ALPHABET) for _ in range(rng.randint(1, 3))]
        evs = build(seq)
        items, dict_evs = [], []
        for i, e in enumerate(evs):
            mode = rng.choice(["ok"] * 6 + ["bad-signature", "no-proved-time", "subject-mismatch"])
            if e["event"] == "compromised":  # a compromise claim is part of the statement
                e["claimed"] = e["claimed"].replace(microsecond=0)
            pred = {}
            if e["event"] == "rotated":
                pred["successorPublicKeyHex"] = keys[e["successor"]][2].hex()
            if e["event"] == "compromised":
                pred["compromisedNotBefore"] = C.fmt_time(e["claimed"])
            gen = C.fmt_time(e["E"] - timedelta(seconds=3601))
            block = C.fmt_time(e["E"] - timedelta(seconds=7200))
            bundle, st = B.key_event(e["event"], target=keys[e["target"]], signer=keys[e["signer"]], gen=gen, block=block, **pred)
            d = dict(e)
            if mode == "bad-signature":
                payload = B.base64.b64decode(bundle["envelope"]["payload"])
                bundle["envelope"]["payload"] = B.base64.b64encode(payload.replace(b'"event"', b'"event" ', 1)).decode()
                d["sigok"] = False
            elif mode == "no-proved-time":
                bundle["timeEvidence"] = bundle["timeEvidence"][:1]
                d["E"] = None
            elif mode == "subject-mismatch":
                st["subject"][0]["digest"]["sha256"] = C.sha(B.PUB_CO if e["target"] != S2 else B.PUB)
                env, sigs = B.envelope(st, signers=(keys[e["signer"]],))
                bundle = B.bundle_of(env, [B.tsa(sigs[0], "a", gen), B.ots(sigs[0], block)], keys=(keys[e["signer"]],))
                d = None
            items.append((bundle, f"sample-{i}"))
            if d is not None:
                dict_evs.append(d)
        # Identity rule (design 8): the same signed statement supplied twice is one event with its earliest
        # proved time. Apply it to the dictionary side too, so both paths model the same events.
        merged = {}
        for d in dict_evs:
            key = (d["event"], d["target"], d["signer"], d["successor"], d["claimed"], d["sigok"])
            cur = merged.get(key)
            if cur is None or (d["E"] is not None and (cur["E"] is None or d["E"] < cur["E"])):
                merged[key] = d
        dict_evs = list(merged.values())
        out = set()
        loaded = C.load_event_bundles(items, copy.deepcopy(B.POLICY), True, out)
        # The loaded events carry real payload digests; compare outcomes by (event, target, signer, E).
        def summary(es):
            res, ok, ap = C.evaluate_events(es, POLICY)
            by = {e["hash"]: (e["event"], e["target"], e["signer"], C.fmt_time(e["E"]) or "-") for e in es}
            tr = tuple(C.signer_trust(k, "valid", {"quorum": T0 + timedelta(days=400), "anyRoot": None}, POLICY, ok, ap) for k in (K, S, S2, A))
            return sorted((by[r["eventSha256"]], r["outcome"]) for r in res), tr
        for le in loaded:  # map the builder's real keys back to the enumeration's key names
            le["target"] = {C.sha(v[2]): k for k, v in keys.items()}[le["target"]]
            le["signer"] = {C.sha(v[2]): k for k, v in keys.items()}.get(le["signer"], le["signer"])
            if le["successor"]:
                le["successor"] = {C.sha(v[2]): k for k, v in keys.items()}[le["successor"]]
        if summary(loaded) != summary(dict_evs):
            mismatches += 1
            if mismatches <= 5:
                print("LOADING MISMATCH ::", seq)
                print("   loaded:", summary(loaded))
                print("   dicts :", summary(dict_evs))
                print("   out   :", sorted(out))
    print(f"loading sample: {n} sequences rebuilt as signed bundles (with tampered, single-source and subject-mismatch events); {mismatches} mismatches")
    return mismatches == 0


def _worker(args):
    start, stop, length = args
    bad = []
    for seq in itertools.islice(itertools.product(ALPHABET, repeat=length), start, stop):
        p = check(seq)
        if p:
            bad.append((sorted(set(p)), seq))
    return stop - start, bad


def _sample_worker(args):
    seed, count = args
    rng = random.Random(seed)
    bad = []
    for _ in range(count):
        seq = tuple(rng.choice(ALPHABET) for _ in range(4))
        p = check(seq)
        if p:
            bad.append((sorted(set(p)), seq))
    return count, bad


def main(argv):
    quick = "--quick" in argv
    started = time.time()
    if not mutation_check((1, 2)):
        print("FAIL: the invariants did not catch a weakened rule set")
        return 1
    checked, violations = 0, []
    jobs = []
    for length in (1, 2, 3) if not quick else (1, 2):
        total = len(ALPHABET) ** length
        chunk = max(1, total // 64)
        jobs += [(i, min(i + chunk, total), length) for i in range(0, total, chunk)]
    sample_jobs = [] if quick else [(1000 + i, 2000) for i in range(100)]
    with multiprocessing.Pool(os.cpu_count()) as pool:
        for n, bad in pool.imap_unordered(_worker, jobs):
            checked += n
            violations += bad
        sampled = 0
        for n, bad in pool.imap_unordered(_sample_worker, sample_jobs):
            sampled += n
            violations += bad
    for p, seq in violations[:20]:
        print("VIOLATION", p, "::", " ; ".join("/".join(str(x) for x in s if x is not None) for s in seq))
    ok_loading = loading_sample(40 if quick else 300)
    print(f"{checked} sequences of length 1-{2 if quick else 3} (exhaustive) and {0 if quick else sampled} sampled sequences of length 4, "
          f"over {len(ALPHABET)} symbols; {len(violations)} with violations; {time.time() - started:.0f} s")
    return 1 if violations or not ok_loading else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
