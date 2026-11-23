#!/usr/bin/env python3
"""Merge a content batch (questions, cards, topics) into index.html. Idempotent: items are matched by id.

Usage: python3 tools/add_content.py tools/c03_batch1.py [--no-shuffle] [--replace]

New questions get their options shuffled (deterministically, seeded by the question id) so that the correct answer
is not always first and not always the longest. The script validates every item before it writes anything.
"""
import importlib.util
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(os.path.dirname(HERE), "index.html")


def load_batch(path):
    spec = importlib.util.spec_from_file_location("batch", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ser(d):
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


def shuffle_question(q, target=None):
    """Shuffle options (seeded by id). For single-answer questions, `target` pins the correct answer's position."""
    rnd = random.Random(q["id"])
    n = len(q["o"])
    if isinstance(q["a"], list) or target is None:
        order = list(range(n))
        rnd.shuffle(order)
    else:
        rest = [i for i in range(n) if i != q["a"]]
        rnd.shuffle(rest)
        order = rest[:target] + [q["a"]] + rest[target:]
    correct = q["a"] if isinstance(q["a"], list) else [q["a"]]
    new_o = [q["o"][i] for i in order]
    new_correct = sorted(order.index(i) for i in correct)
    q["o"] = new_o
    q["a"] = new_correct if isinstance(q["a"], list) else new_correct[0]


def validate(D, Q, C, topics):
    errs = []
    known_q = {x["id"] for x in D["Q"]}
    known_c = {x["id"] for x in D["C"]}
    seen_text = {re.sub(r"\W+", " ", x["q"].lower()) for x in D["Q"]}
    domains = set(D["DOMAINS"])
    all_topics = set(D["TOPICS"]) | set(topics)
    for q in Q:
        where = "Q%s" % q.get("id")
        multi = isinstance(q["a"], list)
        if q["d"] not in domains:
            errs.append(where + ": unknown domain " + q["d"])
        if q["t"] not in all_topics:
            errs.append(where + ": unknown topic " + str(q["t"]))
        if multi and len(q["o"]) < 5:
            errs.append(where + ": multi-select needs at least 5 options")
        if not multi and len(q["o"]) != 4:
            errs.append(where + ": single answer needs exactly 4 options")
        idx = q["a"] if multi else [q["a"]]
        if any((not isinstance(i, int)) or i < 0 or i >= len(q["o"]) for i in idx):
            errs.append(where + ": answer index out of range")
        if multi and len(set(idx)) != len(idx):
            errs.append(where + ": duplicate answer indexes")
        if len(set(q["o"])) != len(q["o"]):
            errs.append(where + ": duplicate options")
        if not q.get("e"):
            errs.append(where + ": missing explanation")
        key = re.sub(r"\W+", " ", q["q"].lower())
        if key in seen_text and q["id"] not in known_q:
            errs.append(where + ": duplicate question text")
        seen_text.add(key)
    ids = [q["id"] for q in Q]
    if len(ids) != len(set(ids)):
        errs.append("duplicate question ids in batch")
    for c in C:
        if c["t"] not in all_topics:
            errs.append("C%s: unknown topic %s" % (c["id"], c["t"]))
        if not c["f"] or not c["b"]:
            errs.append("C%s: empty side" % c["id"])
    cids = [c["id"] for c in C]
    if len(cids) != len(set(cids)):
        errs.append("duplicate card ids in batch")
    return errs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    batch = load_batch(args[0])
    s = open(INDEX, encoding="utf-8").read()
    m = re.search(r"var D = (\{.*?\});\n", s, re.S)
    raw = m.group(1)
    D = json.loads(raw)
    assert ser(D) == raw, "serialization would change the existing data line"

    Q = json.loads(json.dumps(batch.Q))
    C = json.loads(json.dumps(batch.C))
    topics = getattr(batch, "TOPICS", {})
    base = dict(D)
    if "--replace" in sys.argv:
        qids, cids = {q["id"] for q in Q}, {c["id"] for c in C}
        base["Q"] = [x for x in D["Q"] if x["id"] not in qids]
        base["C"] = [x for x in D["C"] if x["id"] not in cids]
    errs = validate(base, Q, C, topics)
    if errs:
        sys.exit("Validation failed:\n  " + "\n  ".join(errs))

    if "--no-shuffle" not in sys.argv:
        # even spread of the correct position across single-answer questions: blocks of 4 in a seeded random order
        singles = [q for q in Q if not isinstance(q["a"], list)]
        targets = []
        rnd = random.Random(len(Q) * 7919)
        while len(targets) < len(singles):
            block = [0, 1, 2, 3]
            rnd.shuffle(block)
            targets.extend(block)
        tmap = {q["id"]: targets[i] for i, q in enumerate(singles)}
        for q in Q:
            shuffle_question(q, tmap.get(q["id"]))

    if "--replace" in sys.argv:  # re-merge a corrected batch: drop the existing items with the same ids first
        qids, cids = {q["id"] for q in Q}, {c["id"] for c in C}
        D["Q"] = [x for x in D["Q"] if x["id"] not in qids]
        D["C"] = [x for x in D["C"] if x["id"] not in cids]
    known_q = {x["id"] for x in D["Q"]}
    known_c = {x["id"] for x in D["C"]}
    addq = [q for q in Q if q["id"] not in known_q]
    addc = [c for c in C if c["id"] not in known_c]
    D["Q"].extend(addq)
    D["C"].extend(addc)
    for k, v in topics.items():
        D["TOPICS"].setdefault(k, v)
    s = s.replace("var D = " + raw + ";\n", "var D = " + ser(D) + ";\n", 1)
    open(INDEX, "w", encoding="utf-8").write(s)
    print("added %d questions, %d cards (skipped %d questions, %d cards already present)" %
          (len(addq), len(addc), len(Q) - len(addq), len(C) - len(addc)))
    print("totals: %d questions, %d cards" % (len(D["Q"]), len(D["C"])))


if __name__ == "__main__":
    main()
