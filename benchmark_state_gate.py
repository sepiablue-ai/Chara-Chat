import json
import sys
import time
from pathlib import Path

from chat_engine import ChatEngine


SAMPLES = {
    "known": "海に到着！うわー、めちゃくちゃ綺麗な砂浜じゃん！",
    "unknown_cached": "住宅街の小さなプラネタリウムで、紺色のニットワンピースのまま星を見上げよう",
    "unknown_new": "水族館のバックヤードで、透明な飼育員エプロンをつけてクラゲ水槽の配管を点検しよう",
}


def resolve_once(engine, text):
    rule = engine._infer_explicit_scene_transition(text)
    registry = engine._registry_transition_candidate(text)
    dynamic = None
    if engine._needs_dynamic_inference(text, rule, registry):
        dynamic = engine._infer_dynamic_scene_transition(text)
    transition = engine._resolve_scene_transition(
        engine._resolve_scene_transition(rule, registry), dynamic
    )
    return {
        "rule": rule,
        "registry": registry,
        "dynamic": dynamic,
        "transition": transition,
    }


def main():
    names = sys.argv[1:] or list(SAMPLES)
    engine = ChatEngine()
    rows = []
    for name in names:
        text = SAMPLES[name]
        engine.reset_state()
        start = time.time()
        result = resolve_once(engine, text)
        elapsed = time.time() - start
        transition = result["transition"] or {}
        rows.append(
            {
                "name": name,
                "seconds": round(elapsed, 2),
                "source": transition.get("source"),
                "location": transition.get("location"),
                "clothing": transition.get("clothing"),
                "called_dynamic": bool(result["dynamic"]),
            }
        )
    out = Path("testcase_results") / "state_gate_benchmark.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
