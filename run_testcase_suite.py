import json
import re
import sys
from pathlib import Path

from chat_engine import ChatEngine


TURN_PATTERN = re.compile(
    r"ユーザー:\s*「(?P<user>.*?)」\s*シーン:\s*(?P<scene>.*?)\s*服装:\s*(?P<clothing>.*?)(?=\n\s*ユーザー:|\n\s*---|\n\s*##|\n\s*###|\Z)",
    re.DOTALL,
)


def normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def load_cases(root):
    cases = []
    for path in sorted(Path(root).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        headings = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^#+\s*(.+)$", text, re.MULTILINE)]
        matches = list(TURN_PATTERN.finditer(text))
        grouped = {}
        for match in matches:
            title = path.stem
            for pos, heading in headings:
                if pos < match.start() and "テストケース" in heading:
                    title = heading
            grouped.setdefault(title, []).append(
                {
                    "user": normalize(match.group("user")),
                    "expected_scene": normalize(match.group("scene")),
                    "expected_clothing": normalize(match.group("clothing")),
                }
            )
        for title, turns in grouped.items():
            cases.append({"file": str(path), "title": title, "turns": turns})
    return cases


def token_score(expected, actual, tags):
    expected = normalize(expected).lower()
    haystack = f"{actual} {tags}".lower()
    tokens = [
        t
        for t in re.split(r"[・（）()、,\s/＋+]+", expected)
        if len(t) >= 2 and t not in {"シーン", "服装", "あり", "なし", "など"}
    ]
    if not tokens:
        return 0.0, []
    matched = [token for token in tokens if token.lower() in haystack]
    return len(matched) / len(tokens), matched


def run_case(case, image=True):
    character = Path("prompts/character_setting.md").read_text(encoding="utf-8")
    director = Path("prompts/main_ai_director.md").read_text(encoding="utf-8")
    engine = ChatEngine()
    engine.config["llm"]["max_tokens"] = 1600
    engine.initialize_session(character, director)
    results = []
    for index, turn in enumerate(case["turns"], 1):
        final = None
        for final in engine.process_chat_turn_stream(
            turn["user"], enable_image=image, enable_voice=False
        ):
            pass
        scene_score, scene_hits = token_score(
            turn["expected_scene"], final.get("location"), final.get("tags")
        )
        clothing_score, clothing_hits = token_score(
            turn["expected_clothing"], final.get("clothing"), final.get("tags")
        )
        results.append(
            {
                "turn": index,
                "user": turn["user"],
                "expected_scene": turn["expected_scene"],
                "expected_clothing": turn["expected_clothing"],
                "location": final.get("location"),
                "clothing": final.get("clothing"),
                "state_changes": final.get("state_changes"),
                "tags": final.get("tags"),
                "image_path": final.get("image_path"),
                "scene_score": scene_score,
                "scene_hits": scene_hits,
                "clothing_score": clothing_score,
                "clothing_hits": clothing_hits,
                "auto_ok": scene_score >= 0.35 and clothing_score >= 0.25,
            }
        )
    return {
        "file": case["file"],
        "title": case["title"],
        "run_dir": engine.current_run_dir,
        "turns": results,
    }


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "testcase"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    image = "--no-image" not in sys.argv
    cases = load_cases(root)
    if limit:
        cases = cases[:limit]
    out_dir = Path("testcase_results")
    out_dir.mkdir(exist_ok=True)
    summary = []
    for case in cases:
        print(f"=== {Path(case['file']).name} / {case['title']} ({len(case['turns'])} turns) ===", flush=True)
        result = run_case(case, image=image)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{Path(case['file']).stem}_{case['title']}")[:120]
        out_path = out_dir / f"{safe_name}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        bad = [t for t in result["turns"] if not t["auto_ok"]]
        print(f"run_dir={result['run_dir']} bad={len(bad)} output={out_path}", flush=True)
        summary.append(
            {
                "file": result["file"],
                "title": result["title"],
                "run_dir": result["run_dir"],
                "turns": len(result["turns"]),
                "bad": len(bad),
                "output": str(out_path),
            }
        )
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
