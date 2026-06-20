import json
import time
from pathlib import Path

from chat_engine import ChatEngine


CASES = [
    {
        "kind": "known",
        "name": "beach_arrival",
        "user": "海に到着！うわー、めちゃくちゃ綺麗な砂浜じゃん！",
        "expect_location": "sunny_beach",
        "expect_clothing": "summer_dress",
    },
    {
        "kind": "known",
        "name": "school_after_class",
        "user": "やっと今日の授業終わったね！一緒に帰ろ？",
        "expect_location": "classroom_after_school",
        "expect_clothing": "school_uniform",
    },
    {
        "kind": "known",
        "name": "winter_cafe",
        "user": "ここの暖房、ちょっと効きすぎじゃない？ 汗かいてきた",
        "expect_location": "winter_cafe_inside",
        "expect_clothing": "winter_indoor",
    },
    {
        "kind": "unknown",
        "name": "planetarium_cached",
        "user": "住宅街の小さなプラネタリウムで、紺色のニットワンピースのまま星を見上げよう",
        "expect_location_contains": ["planetarium"],
        "expect_clothing_contains": ["knit", "dress"],
    },
    {
        "kind": "unknown",
        "name": "aquarium_cached",
        "user": "水族館のバックヤードで、透明な飼育員エプロンをつけてクラゲ水槽の配管を点検しよう",
        "expect_location_contains": ["aquarium"],
        "expect_clothing_contains": ["keeper", "apron"],
    },
    {
        "kind": "unknown",
        "name": "new_lantern_workshop",
        "user": "古い地下街の紙灯籠工房で、防炎の生成り前掛けと透明ゴーグルをつけて、和紙の骨組みに灯りを入れよう",
        "expect_location_contains": ["lantern", "workshop"],
        "expect_clothing_contains": ["apron", "goggles"],
    },
]


def ok(case, result):
    location = str(result.get("location", "")).lower()
    clothing = str(result.get("clothing", "")).lower()
    tags = str(result.get("tags", "")).lower()
    if case["kind"] == "known":
        return (
            location == case["expect_location"]
            and clothing == case["expect_clothing"]
        )
    loc_ok = all(token in f"{location} {tags}" for token in case["expect_location_contains"])
    cloth_ok = all(token in f"{clothing} {tags}" for token in case["expect_clothing_contains"])
    return loc_ok and cloth_ok


def main():
    character = Path("prompts/character_setting.md").read_text(encoding="utf-8")
    director = Path("prompts/main_ai_director.md").read_text(encoding="utf-8")
    rows = []
    for case in CASES:
        engine = ChatEngine()
        engine.config["llm"]["max_tokens"] = 1600
        engine.initialize_session(character, director)
        start = time.time()
        final = None
        for final in engine.process_chat_turn_stream(
            case["user"], enable_image=False, enable_voice=False
        ):
            pass
        seconds = round(time.time() - start, 2)
        rows.append(
            {
                "kind": case["kind"],
                "name": case["name"],
                "seconds": seconds,
                "ok": ok(case, final),
                "location": final.get("location"),
                "clothing": final.get("clothing"),
                "state_changes": final.get("state_changes"),
                "tags": final.get("tags", "")[:260],
            }
        )
    out = Path("testcase_results") / "known_unknown_3x3_benchmark.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
