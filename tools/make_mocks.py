#!/usr/bin/env python3
"""Build fixed mock exams (D.MOCKS) from the question bank. Deterministic, idempotent (rebuilds all mocks).

Rules for every mock of D.EXAM.n questions:
  * domain counts follow D.EXAM.counts (the DVA-C03 weights)
  * no question appears in two mocks (the bank must be large enough)
  * topics are spread evenly inside a domain (round-robin over topics)
  * questions with several correct answers are shared out evenly
  * AI security questions (topic "ai") get a fixed quota inside the security domain, as task 2.3 does on the exam
Usage: python3 tools/make_mocks.py [number_of_mocks]
"""
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

INDEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
ser = lambda d: json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
AI_QUOTA = 5  # questions on AI security per mock (task 2.3 is roughly 8 percent of the scored content)


def spread(questions, rnd):
    """Order questions so that consecutive picks come from different topics (round-robin, topics in random order)."""
    by_topic = defaultdict(list)
    for q in questions:
        by_topic[q.get("t") or "-"].append(q)
    topics = list(by_topic)
    rnd.shuffle(topics)
    for t in topics:
        rnd.shuffle(by_topic[t])
    out = []
    while any(by_topic.values()):
        for t in topics:
            if by_topic[t]:
                out.append(by_topic[t].pop())
    return out


def main():
    n_mocks = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    s = open(INDEX, encoding="utf-8").read()
    raw = re.search(r"var D = (\{.*?\});\n", s, re.S).group(1)
    D = json.loads(raw)
    assert ser(D) == raw
    counts = D["EXAM"]["counts"]
    rnd = random.Random(20261214)
    picks = [[] for _ in range(n_mocks)]
    rot = 0  # global counter: questions with several correct answers are dealt to the mocks in turn across all domains
    for dom, need in counts.items():
        pool = [q for q in D["Q"] if q["d"] == dom]
        quota = AI_QUOTA if dom == "sec" else 0
        ai = [q for q in pool if q.get("t") == "ai"] if quota else []
        rest = [q for q in pool if q not in ai]
        if len(ai) < quota * n_mocks or len(rest) < (need - quota) * n_mocks:
            sys.exit("not enough questions in domain %s for %d mocks (ai %d, rest %d)" % (dom, n_mocks, len(ai), len(rest)))
        multi = [q for q in rest + ai if isinstance(q["a"], list)]
        rnd.shuffle(multi)
        assigned = [[] for _ in range(n_mocks)]
        for q in multi:
            m = rot % n_mocks
            rot += 1
            assigned[m].append(q)
        ai_single = spread([q for q in ai if not isinstance(q["a"], list)], rnd)
        single_order = spread([q for q in rest if not isinstance(q["a"], list)], rnd)
        for m in range(n_mocks):
            chosen = []
            mine_ai = [q for q in assigned[m] if q.get("t") == "ai"][:quota]
            chosen += mine_ai
            while quota and len([q for q in chosen if q.get("t") == "ai"]) < quota:
                chosen.append(ai_single.pop(0))
            for q in [q for q in assigned[m] if q.get("t") != "ai"]:
                if len(chosen) < need:
                    chosen.append(q)
            while len(chosen) < need:
                chosen.append(single_order.pop(0))
            picks[m].extend(chosen)
    mocks = []
    for m in range(n_mocks):
        qs = picks[m]
        # exam order: interleave domains like a real paper (shuffled, deterministic)
        rnd2 = random.Random(1000 + m)
        rnd2.shuffle(qs)
        mocks.append({"id": "m%d" % (m + 1), "name": "Mock %d" % (m + 1), "ids": [q["id"] for q in qs]})
    # checks
    all_ids = [i for mk in mocks for i in mk["ids"]]
    assert len(all_ids) == len(set(all_ids)), "a question is used twice"
    byid = {q["id"]: q for q in D["Q"]}
    for mk in mocks:
        assert len(mk["ids"]) == D["EXAM"]["n"], mk["id"]
        dc = Counter(byid[i]["d"] for i in mk["ids"])
        assert dict(dc) == counts, (mk["id"], dc)
    D["MOCKS"] = mocks
    s = s.replace("var D = " + raw + ";\n", "var D = " + ser(D) + ";\n", 1)
    open(INDEX, "w", encoding="utf-8").write(s)
    for mk in mocks:
        qs = [byid[i] for i in mk["ids"]]
        print("%s: %d q | domains %s | multi %d | ai %d | topics %d distinct | new-in-C03 batches %d" % (
            mk["name"], len(qs), dict(Counter(q["d"] for q in qs)), sum(isinstance(q["a"], list) for q in qs),
            sum(q.get("t") == "ai" for q in qs), len({q.get("t") for q in qs}), sum(q["id"] > 7000000000 for q in qs)))
    print("questions used: %d of %d" % (len(all_ids), len(D["Q"])))


if __name__ == "__main__":
    main()
