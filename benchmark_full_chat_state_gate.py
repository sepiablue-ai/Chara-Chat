import json
import time
from pathlib import Path

from chat_engine import ChatEngine


SAMPLES = {
    "known": "海に到着！うわー、めちゃくちゃ綺麗な砂浜じゃん！",
    "unknown_cached": "住宅街の小さなプラネタリウムで、紺色のニットワンピースのまま星を見上げよう",
    "unknown_first": "古書修復室の作業台で、綿の修復エプロンと薄い紙手袋をつけて破れたページを直そう",
}


def main():
    character = Path("prompts/character_setting.md").read_text(encoding="utf-8")
    director = Path("prompts/main_ai_director.md").read_text(encoding="utf-8")
    rows = []
    for name, text in SAMPLES.items():
        engine = ChatEngine()
        engine.config["llm"]["max_tokens"] = 1600
        engine.initialize_session(character, director)
        start = time.time()
        final = None
        for final in engine.process_chat_turn_stream(
            text, enable_image=False, enable_voice=False
        ):
            pass
        rows.append(
            {
                "name": name,
                "seconds": round(time.time() - start, 2),
                "location": final.get("location"),
                "clothing": final.get("clothing"),
                "state_changes": final.get("state_changes"),
                "tags": final.get("tags", "")[:180],
            }
        )
    out = Path("testcase_results") / "full_chat_state_gate_benchmark.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

