import json
import sys
from pathlib import Path

from chat_engine import ChatEngine


CASES = {
    "1": [
        "やっと今日の授業終わったね！一緒に帰ろ？",
        "ちょっと歩いたら暑くなってきたな。上着脱いだら？",
        "あそこのカフェで少し宿題していかない？",
        "すっかり暗くなっちゃったね。駅まで送るよ",
        "今日も楽しかった！じゃあ、また明日学校でね",
    ],
    "2": [
        "今からディスコード繋げる？ネトゲのレイドボス行こうぜ",
        "VCの音ちっちゃい？マイク近づけてみて",
        "実は今、お前の家の近くにいるんだよね。お土産あるから突撃していい？",
        "ピンポーン。はーい、開けてー",
        "部屋入るよ。あ、エアコンつけていい？",
    ],
    "3": [
        "海に到着！うわー、めちゃくちゃ綺麗な砂浜じゃん！",
        "よし、俺はもう泳ぐ準備万端！お前も早く水着見せてよ",
        "さすがに泳ぎ疲れたね。海の家で焼きそば食べよ",
        "夕方からやってる地元の夏祭り、このまま行ってみる？",
        "ドーンって大きな音！あ、花火始まったよ！綺麗だね",
    ],
    "4": [
        "先輩、この資料のチェックお願いしてもいいですか？",
        "ふぅ、やっと定時だ。今日のプレゼン、先輩のおかげで大成功でした！",
        "お礼に一杯奢らせてください。近くにいい感じのバーがあるんです",
        "あ、眼鏡外したんですね。そっちの雰囲気も素敵です",
        "結構酔っちゃいましたね。お水もらいましょうか？",
    ],
    "5": [
        "ここの暖房、ちょっと効きすぎじゃない？ 汗かいてきた",
        "じゃあそろそろ出ようか。外、雪降ってきたみたいだよ",
        "うわ、外めちゃくちゃ寒い！風も強いし！",
        "ほら、これ俺のポケットで温めてたカイロ。使いなよ",
        "手、冷たっ！手袋してても冷えるね。繋いで歩こう",
    ],
}


def main():
    case_id = sys.argv[1]
    image_turn = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    turns = CASES[case_id]
    character = Path("prompts/character_setting.md").read_text(encoding="utf-8")
    director = Path("prompts/main_ai_director.md").read_text(encoding="utf-8")
    engine = ChatEngine()
    engine.config["llm"]["max_tokens"] = 1600
    engine.initialize_session(character, director)
    results = []
    for idx, msg in enumerate(turns, 1):
        final = None
        enable_image = image_turn == idx
        for final in engine.process_chat_turn_stream(
            msg, enable_image=enable_image, enable_voice=False
        ):
            pass
        results.append(
            {
                "turn": idx,
                "user": msg,
                "location": final.get("location"),
                "clothing": final.get("clothing"),
                "state_changes": final.get("state_changes"),
                "scene_prompt": final.get("scene_prompt"),
                "dialogue": final.get("character_dialogue"),
            }
        )
    print(json.dumps({"case": case_id, "run_dir": engine.current_run_dir, "turns": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
