import glob
import json


for path in glob.glob("testcase_results/*.json"):
    if path.endswith("summary.json"):
        continue
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print()
    print("##", data["title"], data["run_dir"])
    for turn in data["turns"]:
        tags = turn.get("tags", "")[:160]
        print(
            f"T{turn['turn']} exp=({turn['expected_scene']} / {turn['expected_clothing']}) "
            f"actual=({turn['location']} / {turn['clothing']}) tags={tags}"
        )
