import json
import re
import sys
from pathlib import Path

from chat_engine import ChatEngine
from run_testcase_suite import load_cases


def normalize(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def tokens(text):
    return [
        t
        for t in re.split(r"[・（）()、,\s/＋+]+", normalize(text))
        if len(t) >= 2 and t not in {"シーン", "服装", "あり", "なし", "など"}
    ]


def score(expected, actual, tags):
    haystack = normalize(f"{actual} {tags}")
    parts = tokens(expected)
    if not parts:
        return 0.0, []
    hits = [part for part in parts if part in haystack]
    return len(hits) / len(parts), hits


def apply_turn(engine, user):
    rule = engine._infer_explicit_scene_transition(user)
    registry = engine._registry_transition_candidate(user)
    dynamic = None
    if engine._needs_dynamic_inference(user, rule, registry):
        dynamic = engine._infer_dynamic_scene_transition(user)
    transition = engine._resolve_scene_transition(
        engine._resolve_scene_transition(rule, registry), dynamic
    )
    if transition:
        if transition.get("location_changed") and transition.get("location"):
            engine.current_state["location"] = transition["location"]
        if transition.get("clothing_changed") and transition.get("clothing"):
            engine.current_state["clothing"] = transition["clothing"]
        tags = transition.get("tag_hint", "")
    else:
        tags = ""
    return transition or {}, tags


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "testcase"
    wanted = set(sys.argv[2:]) if len(sys.argv) > 2 else set()
    cases = [
        case for case in load_cases(root)
        if not wanted or Path(case["file"]).name in wanted
    ]
    engine = ChatEngine()
    results = []
    for case in cases:
        engine.reset_state()
        turns = []
        for idx, turn in enumerate(case["turns"], 1):
            transition, tags = apply_turn(engine, turn["user"])
            scene_score, scene_hits = score(
                turn["expected_scene"], engine.current_state["location"], tags
            )
            clothing_score, clothing_hits = score(
                turn["expected_clothing"], engine.current_state["clothing"], tags
            )
            turns.append(
                {
                    "turn": idx,
                    "expected_scene": turn["expected_scene"],
                    "expected_clothing": turn["expected_clothing"],
                    "location": engine.current_state["location"],
                    "clothing": engine.current_state["clothing"],
                    "transition": transition,
                    "tags": tags,
                    "scene_score": scene_score,
                    "scene_hits": scene_hits,
                    "clothing_score": clothing_score,
                    "clothing_hits": clothing_hits,
                    "auto_ok": scene_score >= 0.25 and clothing_score >= 0.20,
                }
            )
        bad = [turn for turn in turns if not turn["auto_ok"]]
        results.append(
            {
                "file": case["file"],
                "title": case["title"],
                "turns": turns,
                "bad": len(bad),
            }
        )
        print(f"{Path(case['file']).name} / {case['title']} bad={len(bad)}")
        print(" | ".join(f"{t['location']}/{t['clothing']}" for t in turns))
    out = Path("testcase_results") / "transition_layer_eval.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
