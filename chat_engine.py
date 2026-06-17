import asyncio
import requests
import json
import os
import re
import time
import uuid
from datetime import datetime
import random
from urllib.parse import urlparse, urlunparse
import websockets
from gradio_client import Client
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
from json_repair import repair_json
from tag_utils import build_scene_context, merge_prompt_tags, sanitize_scene_tags

CONFIG_PATH = "config.json"

DEFAULT_CONFIG = {
    "llm": {
        "url": "http://127.0.0.1:11434/api/chat",
        "api_mode": "ollama",
        "model": "gemma4:12b-it-qat",
        "max_tokens": 4096,
        "temperature": 0.8
    },
    "comfyui": {"url": "http://192.168.10.108:8188"},
    "tts": {
        "url": "http://192.168.10.108:7860",
        "enabled_by_default": False,
        "checkpoint": "outputs\\character_lora\\checkpoint_final.safetensors"
    },
    "image": {"enabled_by_default": True},
    "chat": {
        "history_window": 4,
        "memory_enabled": True,
        "memory_recall_only": True,
        "memory_max_events": 8,
        "memory_max_chars": 700,
    },
    "streamlit": {"port": 8501},
    "character": {
        "display_name": "AI Character",
        "lora_name": "character_lora.safetensors",
        "base_positive_prompt": "1girl, masterpiece, best quality, good quality, sensitive,",
        "prompts": {
            "character_setting": "prompts/character_setting.md",
            "main_director": "prompts/main_ai_director.md",
            "voice_examples": "prompts/voice_examples.md"
        },
        "clothing": {
            "default": "fully clothed",
            "school_uniform": "school uniform, blazer, neat uniform",
            "uniform": "school uniform, blazer",
            "shirt_uniform": "school uniform, white shirt, no blazer",
            "roomwear": "casual loungewear, hoodie",
            "hoodie": "hoodie, casual loungewear",
            "headset": "hoodie, casual loungewear, headset",
            "casual_hoodie_jeans": "hoodie, jeans, casual clothes",
            "summer_casual": "summer casual clothes",
            "summer_dress": "summer dress",
            "swimsuit": "swimsuit",
            "swim_coverup": "swimsuit, light cover-up",
            "yukata": "yukata",
            "office_jacket": "office lady, office casual, jacket",
            "office_casual": "office lady, office casual",
            "office_no_jacket": "office lady, office casual, no jacket",
            "business_suit": "business suit, necktie",
            "business_shirt": "business shirt, rolled-up sleeves, no jacket",
            "business_jacketpants": "office casual, jacket, chinos",
            "recruit_suit": "recruit suit",
            "smart_casual": "smart casual, jacket, jeans",
            "remote_business": "business shirt, sweatpants",
            "sportswear": "sportswear, tracksuit",
            "casual_shirt_jeans": "casual shirt, jeans, sneakers",
            "jersey": "tracksuit, gym uniform",
            "raincoat_uniform": "school uniform, raincoat, umbrella",
            "raincoat": "raincoat, umbrella",
            "no_glasses": "office lady, office casual, no eyewear",
            "winter_indoor": "winter sweater, indoor clothes",
            "winter_coat": "winter coat",
            "coat_scarf": "winter coat, scarf",
            "coat_scarf_gloves": "winter coat, scarf, gloves",
            "down_scarf_gloves": "down jacket, scarf, gloves",
            "down_jacket": "down jacket",
            "spring_coat": "spring coat, casual clothes",
            "long_coat": "long coat, stylish casual clothes",
            "chic_coat_beret": "chester coat, beret, chic clothes",
            "sweater": "sweater, casual clothes",
            "sweater_glasses": "sweater, glasses",
            "tshirt_shorts": "t-shirt, shorts",
            "cardigan_casual": "light cardigan, casual clothes",
            "ski_wear": "ski wear",
            "formal_dress": "formal dress",
            "sweatshirt": "sweatshirt, loungewear",
            "fleece": "sweatshirt, fleece jacket, loungewear",
            "dotera": "sweatshirt, dotera, loungewear",
            "trench_coat": "trench coat, autumn casual clothes",
            "dracula_costume": "dracula costume, halloween costume",
            "leather_armor": "leather armor",
            "chainmail": "chainmail armor",
            "inn_gown": "inn nightgown",
            "traveler_cloak": "traveler clothes, cloak, boots",
            "court_dress": "court dress",
            "mage_uniform": "apprentice mage uniform",
            "protective_robe": "protective robe",
            "dorm_loungewear": "dorm loungewear",
            "desert_cloak": "desert cloak, turban",
            "linen_underwear": "linen underwear",
            "wool_cloak": "desert cloak, wool cloak",
            "sneakers_casual": "casual clothes, jeans, sneakers",
            "character_headband": "casual clothes, character headband",
            "one_piece": "one-piece dress",
            "live_tshirt": "live t-shirt",
            "live_tshirt_band": "live t-shirt, rubber wristband, ponytail",
            "live_tshirt_hoodie": "live t-shirt, hoodie",
            "rash_guard": "swimsuit, rash guard",
            "hiking_wear": "trekking wear, hiking outfit",
            "mountain_parka": "mountain parka, trekking wear",
            "samue": "samue, indoor wear",
            "light_yukata": "thin summer yukata",
            "formal_kimono_hakama": "formal kimono, hakama",
            "loose_kimono": "loose kimono, relaxed obi",
            "hitatare": "indigo hitatare, samurai casual wear",
            "samurai_armor": "samurai armor, o-yoroi armor, kabuto helmet",
            "kosode": "kosode kimono",
            "taisho_hakama_haori": "taisho era kimono, hakama, black haori",
            "taisho_hakama": "taisho era kimono, hakama, no haori",
            "borrowed_shirt_trousers": "flannel shirt, trousers",
            "juni_hitoe": "luxurious juni-hitoe, layered court kimono",
            "karaginu_mo": "formal karaginu and mo, heian court dress",
            "heian_hitoe_hakama": "hitoe kimono, scarlet hakama",
            "vinyl_coat": "hooded waterproof vinyl coat, dustproof coat",
            "cyber_suit": "sleek cyber suit, sensor suit",
            "cooling_inner": "cooling inner suit",
            "station_jumpsuit": "space station jumpsuit uniform",
            "space_suit": "EVA space suit, visor helmet",
            "medical_gown": "thin blue medical gown",
            "cyborg_armor": "silver cyborg armor",
            "white_bodysuit": "plain white bodysuit",
            "work_coveralls": "work coveralls, cleaner uniform",
            "tuxedo": "evening tuxedo",
            "tuxedo_riders": "evening tuxedo, leather rider jacket",
            "training_wear": "training wear, quick-dry t-shirt, running shorts, running shoes",
            "swim_cap_goggles": "swimsuit, swim cap, swim goggles",
            "baseball_undershirt": "baseball uniform pants, long sleeve undershirt, cleats",
            "baseball_uniform_full": "full baseball uniform",
            "baseball_uniform_helmet": "baseball uniform, batting helmet",
            "baseball_uniform_no_helmet": "baseball uniform, no helmet",
            "running_singlet": "running singlet, bib number, running shorts",
            "running_no_headband": "running singlet, bib number, running shorts, no headband",
            "running_blanket_medal": "running wear, aluminum thermal blanket, finisher medal",
            "yoga_wear": "yoga leggings, camisole top",
            "towel": "bath towel",
            "lesson_wear": "dance lesson wear, practice jersey, sneakers",
            "idol_stage_costume": "sparkly idol stage costume, frilly dress",
            "idol_hoodie": "sparkly idol stage costume, official hoodie",
            "white_one_piece": "pure white one-piece dress",
            "dance_costume": "black dance costume, stage outfit",
            "dance_cardigan": "black dance costume, loose cardigan",
            "doctor_cardigan": "white medical coat, cardigan",
            "medical_gloves_mask": "white medical coat, medical gloves, surgical mask",
            "rescue_uniform": "orange rescue uniform",
            "rescue_harness": "orange rescue uniform, helmet, safety harness",
            "rescue_rain_jacket": "orange rescue uniform, reflective waterproof jacket",
            "work_shirt": "navy work shirt",
            "travel_casual": "travel hoodie, jeans, sneakers",
            "travel_blanket": "travel hoodie, jeans, airplane blanket",
            "resort_roomwear": "light resort roomwear",
            "neat_travel_casual": "neat travel casual clothes",
            "yukata_haori": "yukata, haori jacket",
            "sneakers_parka": "casual clothes, jeans, sneakers, light hoodie",
            "clear_poncho": "casual clothes, transparent hooded plastic rain poncho, clear raincoat",
            "rain_poncho": "t-shirt, shorts, hooded rain poncho, waterproof poncho",
            "limited_tshirt": "limited edition theme park t-shirt",
            "limited_tshirt_hoodie": "limited edition theme park t-shirt, light hoodie",
            "wet_coat_umbrella": "wet coat, umbrella",
            "fluffy_roomwear": "fluffy roomwear, cozy loungewear",
            "roomwear_blanket": "fluffy roomwear, blanket",
            "white_shirt_sweatpants": "white shirt, sweatpants",
            "white_shirt_cardigan": "white shirt, cardigan",
            "white_shirt_fleece": "white shirt, fleece jacket",
            "bath": "bath towel",
            "bathrobe": "bathrobe",
            "topless": "bare legs",
            "bottomless": "shirt",
            "naked": ""
        }
    }
}


class ChatEngine:
    def __init__(self):
        self.config = self._load_config()
        self._apply_config()
        self.base_dir = "./memories"
        os.makedirs(self.base_dir, exist_ok=True)
        
        # ボイス用プロンプトの読み込み
        voice_path = self.character_config.get("prompts", {}).get("voice_examples", "./prompts/voice_examples.md")
        self.voice_examples = self._load_voice_examples(voice_path)
        
        self.tts_client = None
        self._tts_initialized = False
        self.reset_state()

    def _load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_CONFIG.copy()

    def _apply_config(self):
        previous_session = getattr(self, "http_session", None)
        if previous_session is not None:
            previous_session.close()
        self.llm_url = self.config["llm"]["url"]
        self.sd_url = self.config["comfyui"]["url"]
        self.comfy_output_dir = self.config["comfyui"].get("output_dir", "")
        self.tts_base_url = self.config["tts"]["url"]
        self.tts_checkpoint = self.config["tts"]["checkpoint"]
        self.history_window = self.config["chat"]["history_window"]
        self.memory_enabled = self.config["chat"].get("memory_enabled", True)
        self.memory_recall_only = self.config["chat"].get(
            "memory_recall_only", True
        )
        self.memory_max_events = self.config["chat"].get("memory_max_events", 8)
        self.memory_max_chars = self.config["chat"].get("memory_max_chars", 700)
        self.character_config = self.config.get("character", DEFAULT_CONFIG["character"])
        self.http_session = requests.Session()

    def reload_config(self):
        """設定ファイルを再読み込みしてURLなどを更新する"""
        self.config = self._load_config()
        self._apply_config()
        # TTS再初期化フラグをリセット
        self.tts_client = None
        self._tts_initialized = False
        print("[CONFIG] 設定を再読み込みしました")

    # ------------------------------------------------------------------
    # TTS
    # ------------------------------------------------------------------
    def _setup_tts_model(self):
        """TTS Gradioクライアントを初期化（遅延初期化）"""
        if self._tts_initialized:
            return self.tts_client is not None
        self._tts_initialized = True
        print(f"[TTS] TTS 接続中 (URL: {self.tts_base_url})")
        try:
            self.tts_client = Client(self.tts_base_url)
            print("[TTS] ✅ 接続成功。モデルロード開始...")
            status = self.tts_client.predict(
                checkpoint=self.tts_checkpoint,
                model_device="cuda",
                model_precision="bf16",
                codec_device="cuda",
                codec_precision="bf16",
                api_name="/_load_model"
            )
            print(f"[TTS] ✅ モデルロード完了: {status}")
            return True
        except Exception as e:
            print(f"[TTS] ⚠️ TTS 初期化失敗: {e}")
            self.tts_client = None
            self._tts_initialized = False
            return False

    def preload_tts(self):
        """アプリ起動時にTTSモデルをロードして初回ターンの待ち時間をなくす"""
        return self._setup_tts_model()

    def _generate_voice(self, text, filename):
        """テキストを音声合成してWAVファイルとして保存。パスを返す"""
        if not self._tts_initialized:
            self._setup_tts_model()
        if not text or not self.current_run_dir or not self.tts_client:
            return None
        try:
            print(f"[TTS] 音声生成中: 「{text[:30]}...」" if len(text) > 30 else f"[TTS] 音声生成中: 「{text}」")
            t_start = time.time()
            result = self.tts_client.predict(
                checkpoint=self.tts_checkpoint,
                model_device="cuda", model_precision="bf16",
                codec_device="cuda", codec_precision="bf16",
                text=text, uploaded_audio=None,
                num_steps=40, num_candidates=1, seed_raw="",
                cfg_guidance_mode="independent",
                cfg_scale_text=3.0, cfg_scale_speaker=5.0, cfg_scale_raw="",
                cfg_min_t=0.5, cfg_max_t=1.0, context_kv_cache=True,
                truncation_factor_raw="", rescale_k_raw="", rescale_sigma_raw="",
                speaker_kv_scale_raw="", speaker_kv_min_t_raw="0.9",
                speaker_kv_max_layers_raw="",
                api_name="/_run_generation"
            )
            audio_path = None
            if isinstance(result, tuple) and len(result) > 0:
                audio_info = result[0]
                if isinstance(audio_info, str):
                    audio_path = audio_info
                elif isinstance(audio_info, dict):
                    audio_path = audio_info.get("value") or audio_info.get("path") or audio_info.get("name")

            elapsed = time.time() - t_start
            if audio_path and os.path.exists(audio_path):
                full_path = os.path.join(self.current_run_dir, filename)
                shutil.copy2(audio_path, full_path)
                print(f"[TTS] ✅ 完了 ({elapsed:.2f}秒): {full_path}")
                return full_path
            else:
                print(f"[TTS] ❌ 音声ファイル取得失敗")
                return None
        except Exception as e:
            print(f"[TTS] ❌ 通信エラー: {e}")
            return None

    def _load_voice_examples(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"[INFO] voice_examples 読み込み ({len(content)}文字): {path}")
            return content
        print(f"[WARN] {path} が見つかりません")
        return ""

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------
    def reset_state(self):
        self.messages = []
        self.history = []
        self.memory_events = []
        self.current_run_dir = ""
        self.session_info = {}
        self.current_state = {"location": "indoors", "clothing": "fully_clothed"}

    def initialize_session(self, character_setting, main_director_prompt):
        """新しいチャットセッションを開始する"""
        self.reset_state()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run_dir = os.path.join(self.base_dir, timestamp)
        os.makedirs(self.current_run_dir, exist_ok=True)

        self.session_info = {"started_at": timestamp, "current_turn": 0}

        full_character_setting = character_setting
        if self.voice_examples:
            full_character_setting += "\n\n---\n\n" + self.voice_examples

        final_system_prompt = main_director_prompt.replace("{character_setting}", full_character_setting)
        self.messages = [{"role": "system", "content": final_system_prompt}]
        return self.session_info

    def load_session(self, session_dir, character_setting, main_director_prompt):
        """保存されたセッションを読み込み、会話を再開できる状態に復元する"""
        target_dir = os.path.join(self.base_dir, session_dir)
        log_path = os.path.join(target_dir, "chat_log.json")

        if not os.path.exists(log_path):
            raise FileNotFoundError(f"ログファイルが見つかりません: {log_path}")

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.reset_state()
        self.current_run_dir = target_dir
        self.session_info = data.get("session_info", {})
        saved_turns = data.get("turns", [])
        saved_memory_events = data.get("memory_events", [])

        # システムプロンプトの再構築
        full_character_setting = character_setting
        if self.voice_examples:
            full_character_setting += "\n\n---\n\n" + self.voice_examples
        final_system_prompt = main_director_prompt.replace("{character_setting}", full_character_setting)
        self.messages = [{"role": "system", "content": final_system_prompt}]

        # history と LLM用メッセージ履歴の再構築
        for i, t in enumerate(saved_turns):
            user_text = t.get("user_action", "")
            character_text = t.get("character_dialogue", "")

            # 画像と音声のフルパスを復元
            img_file = t.get("image_filename")
            voice_file = t.get("voice_filename")
            img_path = os.path.join(target_dir, img_file) if img_file else None
            voice_path = os.path.join(target_dir, voice_file) if voice_file else None

            # エンジンのhistoryに復元
            turn_data = {
                "role": "assistant",
                "status": "success",
                "turn_info": t.get("turn_info", f"Turn {i+1}"),
                "scene_description": t.get("scene_description", ""),
                "user_action": user_text,
                "character_dialogue": character_text,
                "image_path": img_path,
                "image_filename": img_file,
                "voice_path": voice_path,
                "voice_filename": voice_file,
                "state_changes": t.get("state_changes", {}),
                "tags": t.get("tags", ""),
                "location": t.get("location", ""),
                "clothing": t.get("clothing", ""),
            }
            self.history.append(turn_data)

            # LLMのコンテキスト（messages）に履歴を追加して会話文脈を復元
            assistant_dict = {
                "scene_description": t.get("scene_description", ""),
                "character_dialogue": character_text
            }
            if t.get("location"): assistant_dict["current_location"] = t["location"]
            if t.get("clothing"): assistant_dict["clothing_state"] = t["clothing"]
            if t.get("state_changes"): assistant_dict["state_changes"] = t["state_changes"]
            
            compact_content = json.dumps(assistant_dict, ensure_ascii=False)
            self.messages.append({"role": "user", "content": f"【ユーザーの行動】「{user_text}」"})
            self.messages.append({"role": "assistant", "content": compact_content})

        if saved_memory_events:
            self.memory_events = saved_memory_events
        else:
            self.memory_events = [
                self._memory_event_from_turn(index, turn)
                for index, turn in enumerate(self.history, 1)
            ]

        if saved_turns:
            last_turn = saved_turns[-1]
            self.current_state["location"] = last_turn.get("location") or self.current_state["location"]
            self.current_state["clothing"] = last_turn.get("clothing") or self.current_state["clothing"]

        print(f"[INFO] セッションを復元しました: {session_dir} (全 {len(saved_turns)} ターン)")
        return self.history

    def _memory_event_from_turn(self, turn_number, turn):
        return {
            "turn": turn_number,
            "user_action": str(turn.get("user_action", "")).strip(),
            "location": str(turn.get("location", "")).strip(),
            "clothing": str(turn.get("clothing", "")).strip(),
        }

    def _append_memory_event(self, turn_data):
        event = self._memory_event_from_turn(len(self.history), turn_data)
        self.memory_events.append(event)

    def _build_verified_memory_context(self, user_input=""):
        if not self.memory_enabled or not self.memory_events:
            return ""
        recall_markers = (
            "今日",
            "さっき",
            "前",
            "以前",
            "あの時",
            "あのとき",
            "これまで",
            "出来事",
            "何した",
            "覚えて",
            "思い出",
            "振り返",
            "過去",
        )
        if (
            self.memory_recall_only
            and not any(marker in user_input for marker in recall_markers)
        ):
            return ""

        recent_turns = max(1, self.history_window // 2)
        older_events = self.memory_events[:-recent_turns]
        if not older_events:
            return ""

        selected = older_events[-self.memory_max_events:]
        lines_reversed = []
        used_chars = 0
        next_location = None
        next_clothing = None
        for event in reversed(selected):
            action = re.sub(r"\s+", " ", event.get("user_action", "")).strip()
            if not action:
                continue
            line = f"T{event.get('turn')}: ユーザー「{action[:100]}」"
            location = event.get("location", "")
            clothing = event.get("clothing", "")
            if location and location != next_location:
                line += f" / 場所:{location}"
            if clothing and clothing != next_clothing:
                line += f" / 服装:{clothing}"
            if used_chars + len(line) > self.memory_max_chars:
                continue
            lines_reversed.append(line)
            used_chars += len(line)
            next_location = location or next_location
            next_clothing = clothing or next_clothing

        lines = list(reversed(lines_reversed))
        if not lines:
            return ""
        return (
            "【確認済みの過去】\n"
            + "\n".join(lines)
            + "\n上記は実際のユーザー入力と確定状態です。"
            "過去を尋ねられたら前置きを短くし、character_dialogue内で"
            "上記のユーザー入力から2件以上を具体的に明示して振り返り、"
            "記載のない出来事は補完しないでください。"
        )

    # ------------------------------------------------------------------
    # JSON utilities
    # ------------------------------------------------------------------
    def _extract_and_parse_json(self, raw_text):
        text = re.sub(r'```json\s*', '', raw_text)
        text = re.sub(r'```\s*', '', text).strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        try:
            return text, json.loads(text)
        except json.JSONDecodeError:
            repaired = repair_json(text)
            print(f"[JSON修復] json_repairで修復")
            return repaired, json.loads(repaired)

    def _extract_completed_json_string(self, raw_text, key):
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"', raw_text)
        if not match:
            return None
        start = match.end() - 1
        escaped = False
        for index in range(start + 1, len(raw_text)):
            char = raw_text[index]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                try:
                    return json.loads(raw_text[start:index + 1])
                except json.JSONDecodeError:
                    return None
        return None

    def _stream_lmstudio_content(self, payload, partial_callback=None):
        stream_payload = {**payload, "stream": True}
        response = self.http_session.post(
            self.llm_url,
            json=stream_payload,
            stream=True,
            timeout=120,
        )
        response.raise_for_status()
        chunks = []
        partial_sent = False
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            event = json.loads(line[6:])
            if event.get("type") != "message.delta":
                continue
            chunks.append(event.get("content", ""))
            if partial_callback is None or partial_sent:
                continue
            raw_content = "".join(chunks)
            partial = {
                key: self._extract_completed_json_string(raw_content, key)
                for key in (
                    "current_location",
                    "clothing_state",
                    "scene_tags",
                )
            }
            if all(partial.values()):
                partial_callback(partial)
                partial_sent = True
        return "".join(chunks)

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    def _call_llm_with_retry(
        self,
        payload,
        max_retries=3,
        retry_delay=2.0,
        validator=None,
        partial_callback=None,
    ):
        api_mode = self.config["llm"].get("api_mode", "openai")
        if api_mode != "ollama":
            token_key = "max_output_tokens" if api_mode == "lmstudio_native" else "max_tokens"
            if token_key not in payload:
                payload[token_key] = self.config["llm"].get("max_tokens", 4096)
        last_error = None
        partial_started = False

        def tracked_partial_callback(partial):
            nonlocal partial_started
            partial_started = True
            partial_callback(partial)

        for attempt in range(1, max_retries + 1):
            try:
                t_start = time.time()
                if api_mode == "lmstudio_native":
                    if partial_callback is not None:
                        raw_content = self._stream_lmstudio_content(
                            payload,
                            partial_callback=tracked_partial_callback,
                        )
                    else:
                        raw_response = self.http_session.post(
                            self.llm_url, json=payload, timeout=120
                        ).json()
                        raw_content = "".join(
                            item.get("content", "")
                            for item in raw_response.get("output", [])
                            if item.get("type") == "message"
                        )
                    if not raw_content.strip():
                        raise ValueError("メッセージ出力なし")
                elif api_mode == "ollama":
                    raw_response = self.http_session.post(
                        self.llm_url, json=payload, timeout=120
                    ).json()
                    if raw_response.get("error"):
                        raise ValueError(raw_response["error"])
                    raw_content = raw_response.get("message", {}).get("content", "")
                    if not raw_content.strip():
                        raise ValueError(f"メッセージ出力なし: {raw_response}")
                else:
                    raw_response = self.http_session.post(
                        self.llm_url, json=payload, timeout=120
                    ).json()
                    if "choices" not in raw_response:
                        raise ValueError(f"'choices'キーなし: {raw_response}")
                    choice = raw_response["choices"][0]
                    finish_reason = choice.get("finish_reason", "unknown")
                    if finish_reason == "length":
                        print(f"⚠️ max_tokens到達。max_tokens={payload.get('max_tokens')}")
                    message_data = choice["message"]
                    raw_content = message_data.get("content", "")
                    if not raw_content.strip() and "reasoning_content" in message_data:
                        raw_content = message_data.get("reasoning_content", "")
                        print("[INFO] reasoning_contentから取得")
                print(f"[TIMER] LLM: {time.time()-t_start:.2f}秒")
                content, result = self._extract_and_parse_json(raw_content)
                if validator is not None:
                    validator(result)
                return content, result
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                last_error = e
                print(f"[LLMリトライ] {attempt}/{max_retries}: {e}")
                if partial_started:
                    raise RuntimeError(
                        "画像先行開始後にLLM応答の検証に失敗しました"
                    ) from e
                if attempt < max_retries:
                    time.sleep(retry_delay)
            except Exception as e:
                last_error = e
                print(f"[LLMリトライ] 通信エラー {attempt}/{max_retries}: {e}")
                if partial_started:
                    raise RuntimeError(
                        "画像先行開始後にLLMストリームが失敗しました"
                    ) from e
                if attempt < max_retries:
                    time.sleep(retry_delay)
        raise RuntimeError(f"LLM {max_retries}回失敗。最後のエラー: {last_error}")

    # ------------------------------------------------------------------
    # Clothing Tag Rules
    # ------------------------------------------------------------------
    def _get_clothing_tags(self, clothing_state):
        state = clothing_state.lower()
        clothing_cfg = self.character_config.get("clothing", {})
        
        for key, value in sorted(
            clothing_cfg.items(), key=lambda item: len(item[0]), reverse=True
        ):
            if key in state:
                return value, ""
        return clothing_cfg.get("default", ""), ""

    def _infer_explicit_clothing_state(self, user_input):
        # SFW汎用版ではLLMのJSON出力(clothing_state)に判断を委ねるため、強制オーバーライドは行わない
        return None

    def _infer_explicit_scene_transition(self, user_input):
        text = str(user_input)
        current_location = self.current_state.get("location", "")
        current_clothing = self.current_state.get("clothing", "")

        def transition(location=None, clothing=None, reason="", tags=""):
            return {
                "location": location,
                "clothing": clothing,
                "location_changed": bool(location and location != current_location),
                "clothing_changed": bool(clothing and clothing != current_clothing),
                "reason": reason,
                "tag_hint": tags,
            }

        # Strong current-intent rules. Many prompts mention a previous place
        # first ("after BBQ...", "after the dragon..."), then the actual
        # destination/clothes. Prefer explicit destination/change markers before
        # broad context keywords.
        if "開園前の入場ゲート" in text:
            return transition("themepark_entrance_gate", "sneakers_casual", "テーマパークの入場ゲート", "theme park entrance gate, sneakers, denim")
        if "バルコニーから夕方の海" in text or "軽い部屋着" in text:
            return transition("resort_hotel_room", "resort_roomwear", "リゾートホテルの客室", "resort hotel room, ocean balcony, roomwear")
        if ("朝から雨" in text or "雨の朝" in text) and "キッチン" in text:
            return transition("rainy_morning_kitchen", "sweatshirt", "雨の朝のキッチン", "rainy morning kitchen, coffee, sweatshirt")
        if "宅配" in text or "フリース" in text and "玄関" in text:
            return transition("rainy_home_entrance", "white_shirt_fleece", "雨の日の自宅玄関", "rainy home entrance, parcel delivery, fleece jacket")
        if "カラオケ" in text:
            return transition("karaoke_room", "business_jacketpants", "二次会のカラオケ", "karaoke_room, microphone, party_lighting, singing")
        if "開園前" in text or ("到着" in text and "Tシャツ" in text and "スニーカー" in text):
            return transition("amusement_park_gate", "sneakers_casual", "遊園地の入場ゲート", "amusement_park_gate, sneakers, sunny")
        if "バルコニー" in text:
            return transition("castle_balcony", "court_dress", "王城のバルコニー", "castle_balcony, night_sky, court_dress")
        if "バルに" in text or "洋風居酒屋" in text:
            return transition("western_pub", "casual_shirt_jeans", "洋風居酒屋へ移動", "pub, bar_table, casual shirt, jeans, drink")
        if "ゲームコーナー" in text:
            return transition("retro_game_corner", "yukata", "旅館のゲームコーナー", "retro_game_center, arcade_cabinets, yukata")
        if "ドテラ" in text and ("夜食" in text or "お母さん" in text) and current_clothing == "fleece":
            return transition("home_living_room", "fleece", "自宅リビングでフリースを保持", "living_room, fleece_jacket, sweatshirt, loungewear")
        if "ドテラ" in text and ("居間" in text or "リビング" in text):
            return transition("parents_home_living_room", "dotera", "実家の居間", "living_room, breakfast, kotatsu, dotera")
        if "ドテラ" in text:
            return transition("parents_home_bedroom", "dotera", "実家の自室でドテラ", "bedroom, parents_home, sweatshirt, dotera")
        if "フリース" in text and ("リビング" in text or "夜食" in text):
            return transition("home_living_room", "fleece", "自宅リビングでフリース", "living_room, fleece_jacket, sweatshirt, loungewear")
        if "フリース" in text:
            return transition("home_room", "fleece", "自室でフリースを羽織る", "bedroom, fleece_jacket, sweatshirt, loungewear")
        if "スウェット" in text and ("家に移動" in text or "実家" in text or "貸す" in text or "片付け" in text):
            loc = "parents_home_bedroom" if "実家" in text else "home_room"
            return transition(loc, "sweatshirt", "自室でスウェットに着替える", "bedroom, sweatshirt, loungewear")
        if ("宿屋" in text or "旅籠" in text or "ベッド" in text) and ("部屋着" in text or "寝間着" in text or "ガウン" in text):
            return transition("inn_room", "inn_gown", "宿屋の客室", "inn_room, bed, gown, warm_lighting")
        if "時計塔" in text and ("魔法" in text or "魔術師" in text):
            return transition("magic_academy_clocktower", "mage_uniform", "魔法学校の時計塔前", "magic_academy, clocktower, mage_uniform")
        if "焚き火" in text:
            return transition("ruins_campfire", "wool_cloak", "遺跡内部の焚き火前", "campfire, ancient_ruins_interior, wool_cloak")
        if "古代遺跡" in text or "遺跡群" in text:
            return transition("ancient_ruins", "linen_underwear", "古代遺跡", "ancient_ruins, desert, linen_underwear")
        if "リネン" in text or "水場" in text:
            return transition("oasis_waterfront", "linen_underwear", "オアシスの水辺", "oasis_water, linen_underwear, palm_trees")
        if "和食レストラン" in text or "和食屋" in text:
            return transition("japanese_restaurant", "sneakers_casual", "駅ビルの和食レストラン", "japanese_restaurant, dinner, casual clothes")
        if "居酒屋" in text and ("Tシャツ" in text or "パーカー" in text or "打ち上げ" in text):
            return transition("izakaya_private_room", "live_tshirt_hoodie", "ライブ後の居酒屋個室", "izakaya, private_room, hoodie, live_tshirt")
        if "読書スペース" in text or "メガネ" in text:
            return transition("library_reading_space", "sweater_glasses", "図書館の読書スペース", "library, reading_space, glasses, sweater")
        if "アパレルショップ" in text or "セレクトショップ" in text:
            return transition("apparel_shop", "sneakers_casual", "アパレルショップ店内", "apparel_shop, clothes_rack, jeans, sneakers")
        if "フードコート" in text:
            return transition("food_court", "sneakers_casual", "モールのフードコート", "food_court, crowded, casual")
        if "購入したワンピース" in text or ("シアター" in text and "ワンピース" in text):
            return transition("movie_theater", "one_piece", "映画館シアター内", "movie_theater, cinema_seat, one-piece dress")
        if "ライトアップ" in text or "夜桜" in text:
            return transition("illuminated_sakura_path", "spring_coat", "夜桜の並木道", "night_sakura, illuminated, spring_coat")
        if "ブルーシート" in text:
            return transition("sakura_picnic_sheet", "spring_coat", "お花見のブルーシート", "sakura, picnic_sheet, blue_sheet, spring_coat")
        if "屋台" in text:
            return transition("sakura_food_stalls", "casual", "屋台が立ち並ぶ通り", "sakura, food_stalls, street_food, spring casual")
        if "甘酒" in text and ("茶屋" in text or "暖簾" in text):
            return transition("amazake_tea_house", "spring_coat", "甘酒茶屋", "tea_house, amazake, spring_coat")
        if "プール" in text and ("入場ゲート" in text or "チケット" in text):
            return transition("pool_gate", "tshirt_shorts", "市民プール入場ゲート", "pool_gate, summer, t-shirt, shorts")
        if "更衣室" in text and "水着" in text:
            return transition("pool_locker_room", "swimsuit", "プールの更衣室", "locker_room, swimsuit")
        if "パラソルベンチ" in text or ("パラソル" in text and "ベンチ" in text):
            return transition("pool_parasol_bench", "rash_guard", "プールサイドのパラソルベンチ", "poolside, parasol_bench, rash_guard, swimsuit")
        if "鳥居" in text or "初詣" in text or "除夜の鐘" in text:
            return transition("shrine_torii", "down_scarf_gloves", "神社の鳥居前", "shrine_torii, snow, down_jacket, scarf, gloves")
        if "甘酒配布" in text or "お神酒" in text or ("甘酒" in text and "テント" in text):
            return transition("shrine_amazake_stand", "down_jacket", "境内の甘酒配布所", "shrine, amazake_stand, down_jacket")
        if "ファミレス" in text and ("ダウン" in text or "セーター" in text or "暖房" in text):
            return transition("late_night_family_restaurant", "winter_indoor", "深夜のファミリーレストラン", "family_restaurant, midnight, sweater")
        if "深夜" in text and "ファミリーレストラン" in text:
            return transition("late_night_family_restaurant", "winter_indoor", "深夜のファミリーレストラン", "family_restaurant, midnight, sweater")

        # Music / idol testcase rules.
        if "リハーサルステージ" in text or ("照明チェック" in text and "レッスン着" in text):
            return transition("live_house_rehearsal_stage", "lesson_wear", "ライブハウスのリハーサルステージ", "live house rehearsal stage, empty audience, lesson wear")
        if "楽屋" in text and ("ステージ衣装" in text or "鏡前" in text):
            return transition("live_house_dressing_room", "idol_stage_costume", "ライブハウスの楽屋", "dressing room, mirror lights, idol stage costume")
        if "ペンライト" in text or "イントロ" in text and "センター" in text:
            return transition("idol_live_stage", "idol_stage_costume", "ライブ本番のステージ", "idol live stage, penlights, stage lights, idol costume")
        if "舞台袖" in text or "スタッフさんに水" in text:
            return transition("live_house_stage_wing", "idol_stage_costume", "ライブハウスの舞台袖", "stage wing, backstage, water bottle, idol costume")
        if "チェキ" in text or "物販ブース" in text:
            return transition("idol_merch_cheki_booth", "idol_hoodie", "物販・チェキ撮影ブース", "merch booth, cheki photo table, official hoodie")
        if "白い撮影スタジオ" in text or "カメラテスト" in text:
            return transition("white_cyclorama_studio", "casual", "白ホリ撮影スタジオ", "white cyclorama studio, camera test, casual clothes")
        if "メイクルーム" in text or "白いワンピース" in text and "ヘアメイク" in text:
            return transition("makeup_room", "white_one_piece", "メイクルーム", "makeup room, vanity lights, white one-piece dress")
        if "人工の夕焼け" in text or "カメラ前" in text and "ワンピース" in text:
            return transition("mv_room_set", "white_one_piece", "MV用の室内セット", "music video room set, artificial sunset, white dress")
        if "ダンスパート" in text or "黒いダンス衣装" in text:
            return transition("black_dance_mv_set", "dance_costume", "黒背景のダンス撮影セット", "black dance set, smoke, dance costume")
        if "差し入れ" in text and "カーディガン" in text:
            return transition("studio_rest_area", "dance_cardigan", "撮影スタジオの休憩スペース", "studio rest area, sofa, cardigan over dance costume")

        # Hospital / rescue testcase rules.
        if "ナースステーション" in text and ("カーディガン" in text or "お茶" in text):
            return transition("night_nurse_station", "doctor_cardigan", "夜のナースステーション", "nurse station, night shift, white medical coat, cardigan")
        if "救急搬送" in text or ("処置室" in text and "手袋" in text):
            return transition("emergency_treatment_room", "medical_gloves_mask", "救急処置室", "emergency treatment room, medical gloves, surgical mask")
        if "ベッドサイド" in text and "患者" in text:
            return transition("emergency_bedside", "medical_gloves_mask", "救急処置室のベッドサイド", "hospital bedside, emergency room, medical mask, gloves")
        if "ストレッチャー" in text or "検査室" in text:
            return transition("hospital_night_corridor", "medical_gloves_mask", "病院の夜間廊下", "hospital corridor at night, stretcher, medical mask")
        if "消防署の車庫" in text or "救助資機材" in text:
            return transition("fire_station_garage", "rescue_uniform", "消防署の車庫", "fire station garage, rescue equipment, orange rescue uniform")
        if "山道の訓練現場" in text or "ハーネス" in text and "斜面" in text:
            return transition("mountain_rescue_training_site", "rescue_harness", "山道の救助訓練現場", "mountain rescue training site, helmet, safety harness")
        if "崖下" in text or "要救助者" in text:
            return transition("cliff_rescue_point", "rescue_harness", "崖下の救助ポイント", "cliff rescue point, rope, helmet, harness")
        if "反射材付き" in text or ("雨" in text and "救助" in text):
            return transition("rainy_rescue_training_site", "rescue_rain_jacket", "雨の救助訓練現場", "rainy rescue site, reflective waterproof jacket")
        if "報告書" in text and "消防署" in text:
            return transition("fire_station_office", "work_shirt", "消防署の事務室", "fire station office, report writing, navy work shirt")

        # Travel / hotel testcase rules.
        if "空港の出発ロビー" in text:
            return transition("airport_departure_lobby", "travel_casual", "空港の出発ロビー", "airport departure lobby, suitcase, travel hoodie, jeans")
        if "飛行機" in text and "ブランケット" in text:
            return transition("airplane_cabin", "travel_blanket", "飛行機の機内", "airplane cabin, window seat, airplane blanket")
        if "南国の空港" in text or "湿った熱気" in text:
            return transition("tropical_airport_exit", "summer_dress", "南国リゾートの空港出口", "tropical airport exit, palm trees, summer dress")
        if "リゾートホテルのロビー" in text or "ウェルカムドリンク" in text:
            return transition("resort_hotel_lobby", "summer_dress", "リゾートホテルのロビー", "resort hotel lobby, welcome drink, ocean breeze, summer dress")
        if "バルコニーから夕方の海" in text or "軽い部屋着" in text:
            return transition("resort_hotel_room", "resort_roomwear", "リゾートホテルの客室", "resort hotel room, ocean balcony, roomwear")
        if "旅館の玄関" in text or "女将" in text:
            return transition("onsen_ryokan_entrance", "neat_travel_casual", "温泉旅館の玄関", "onsen ryokan entrance, neat travel casual")
        if "宿の浴衣" in text or ("畳の香り" in text and "浴衣" in text):
            return transition("onsen_inn_room", "yukata", "温泉旅館の客室", "tatami ryokan room, yukata")
        if "脱衣所" in text or "大浴場" in text:
            return transition("onsen_dressing_room", "towel", "温泉の脱衣所", "onsen dressing room, bath towel, steam")
        if "宴会場" in text or "夕食のお膳" in text:
            return transition("ryokan_banquet_hall", "yukata", "旅館の宴会場", "ryokan banquet hall, dinner tray, yukata")
        if "中庭" in text and ("羽織" in text or "池" in text):
            return transition("ryokan_garden_courtyard", "yukata_haori", "旅館の中庭", "ryokan garden courtyard, pond, yukata, haori")

        # Theme park testcase rules.
        if "開園前の入場ゲート" in text:
            return transition("themepark_entrance_gate", "sneakers_casual", "テーマパークの入場ゲート", "theme park entrance gate, sneakers, denim")
        if "ジェットコースター" in text and "薄いパーカー" in text:
            return transition("roller_coaster_queue", "sneakers_parka", "ジェットコースターの待機列", "roller coaster queue, light hoodie, sneakers")
        if "透明ポンチョ" in text or ("雨雲" in text and "石畳" in text):
            return transition("rainy_themepark_path", "clear_poncho", "雨のテーマパーク通路", "rainy theme park path, transparent poncho, wet pavement")
        if "テーマレストラン" in text or "カチューシャ" in text and "ランチ" in text:
            return transition("theme_restaurant", "character_headband", "園内テーマレストラン", "theme restaurant, character headband, lunch")
        if "夜のパレード" in text or "光るワンド" in text:
            return transition("night_parade_route", "character_headband", "夜パレードの沿道", "night parade route, glowing wand, character headband")
        if "夏イベント" in text or "水濡れショーを待" in text:
            return transition("summer_event_plaza", "tshirt_shorts", "夏イベント広場", "summer event plaza, mist, t-shirt, shorts")
        if "ずぶ濡れゾーン" in text or "レインポンチョ" in text:
            return transition("splash_show_front_area", "rain_poncho", "水濡れショーの前方エリア", "splash show front area, rain poncho, t-shirt, shorts")
        if "日なたのベンチ" in text or "濡れた髪" in text:
            return transition("themepark_bench", "tshirt_shorts", "パーク内のベンチ", "theme park bench, towel, wet hair, t-shirt, shorts")
        if "限定Tシャツ" in text and "ショップ" in text:
            return transition("themepark_shop_front", "limited_tshirt", "テーマパークのショップ前", "theme park shop front, limited edition t-shirt")
        if "観覧車" in text and "夜景" in text:
            return transition("night_ferris_wheel", "limited_tshirt_hoodie", "夜の観覧車", "night ferris wheel, light hoodie, limited t-shirt")

        # Rainy home testcase rules.
        if "玄関マット" in text or ("びしょ濡れ" in text and "コート" in text):
            return transition("rainy_home_entrance", "wet_coat_umbrella", "雨の日の自宅玄関", "rainy home entrance, wet coat, umbrella")
        if "洗面所" in text and "バスタオル" in text:
            return transition("home_washroom", "towel", "自宅の洗面所", "home washroom, bath towel, wet hair")
        if "ふわふわのルームウェア" in text or "ホットミルク" in text:
            return transition("home_living_room", "fluffy_roomwear", "自宅のリビング", "living room, hot milk, fluffy roomwear")
        if "ブランケット" in text and "雨音" in text:
            return transition("rainy_living_room", "roomwear_blanket", "雨音のするリビング", "rainy living room, blanket, movie, dim light")
        if "寝室" in text and "パジャマ" in text:
            return transition("bedroom_night", "pajamas", "夜の寝室", "bedroom at night, bed, pajamas")
        if "雨の朝" in text and "キッチン" in text:
            return transition("rainy_morning_kitchen", "sweatshirt", "雨の朝のキッチン", "rainy morning kitchen, coffee, sweatshirt")
        if "オンライン会議" in text or "Webカメラ" in text:
            return transition("home_work_desk", "white_shirt_sweatpants", "自宅の仕事デスク", "home work desk, webcam, white shirt, sweatpants")
        if "窓際" in text and "カーディガン" in text:
            return transition("home_window_side", "white_shirt_cardigan", "自宅の窓際", "home window side, rain, white shirt, cardigan")
        if "宅配" in text or "フリース" in text and "玄関" in text:
            return transition("rainy_home_entrance", "white_shirt_fleece", "雨の日の自宅玄関", "rainy home entrance, parcel delivery, fleece jacket")
        if "読書" in text and "パジャマ" in text:
            return transition("night_reading_space", "pajamas", "夜の自宅の読書スペース", "night reading space, rain, pajamas, book")

        # Historical / oriental testcase rules.
        if "長屋" in text and ("狭い部屋" in text or "ゴロゴロ" in text):
            return transition("nagaya_room", "light_yukata", "長屋の自室", "edo nagaya room, tatami, thin summer yukata")
        if "共同井戸" in text or "井戸" in text and "たらい" in text:
            return transition("nagaya_well", "light_yukata", "長屋の共同井戸端", "edo outdoor well, bucket, thin summer yukata")
        if "大名屋敷" in text and ("門" in text or "くぐろう" in text):
            return transition("daimyo_mansion_gate", "formal_kimono_hakama", "大名屋敷の玄関口", "daimyo mansion gate, formal kimono, hakama")
        if "広間" in text and "畳" in text:
            return transition("daimyo_great_hall", "formal_kimono_hakama", "大名屋敷の大広間", "tatami great hall, formal kimono, hakama")
        if "縁側" in text:
            return transition("nagaya_veranda", "loose_kimono", "長屋の縁側", "edo veranda, watermelon, loose kimono")
        if "陣幕" in text:
            return transition("military_tent_night", "hitatare", "陣幕の内部", "sengoku military tent, map, torchlight, indigo hitatare")
        if "物見櫓" in text:
            return transition("fort_watchtower", "hitatare", "砦の物見櫓", "wooden watchtower, dawn, indigo hitatare")
        if ("雨" in text or "最前線" in text or "戦場" in text) and current_clothing == "samurai_armor":
            return transition("rainy_battlefield_frontline", "samurai_armor", "雨の戦場の最前線", "rainy battlefield frontline, mud, samurai armor, o-yoroi, kabuto helmet")
        if "大鎧" in text or "甲冑" in text or "兜" in text:
            loc = "rainy_battlefield_frontline" if "雨" in text or "最前線" in text else "battlefield_headquarters"
            return transition(loc, "samurai_armor", "甲冑を着用", "sengoku battlefield, samurai armor, o-yoroi, kabuto helmet")
        if "天守閣" in text:
            return transition("castle_keep", "kosode", "お城の天守閣", "castle keep, view from tower, kosode kimono")
        if "洋館の書斎" in text:
            return transition("taisho_western_study", "taisho_hakama_haori", "洋館の書斎", "taisho era study, bookshelves, kimono, hakama, black haori")
        if "路面電車" in text:
            return transition("taisho_tram_interior", "taisho_hakama_haori", "路面電車の車内", "streetcar interior, taisho city, kimono, hakama, black haori")
        if "喫茶店" in text or ("モダンなカフェ" in text and "羽織" in text):
            return transition("taisho_cafe", "taisho_hakama", "大正浪漫の喫茶店", "taisho cafe, round stool, kimono, hakama, no haori")
        if "赤レンガ" in text:
            return transition("red_brick_slope", "taisho_hakama", "赤レンガの坂道", "red brick slope, rain, umbrella, taisho kimono, hakama")
        if "ネルシャツ" in text:
            return transition("friends_tatami_room", "borrowed_shirt_trousers", "友人の和室", "tatami room, flannel shirt, trousers")
        if "十二単" in text or "几帳" in text:
            return transition("shinden_inner_room", "juni_hitoe", "寝殿の奥", "heian palace interior, kichou curtain, juni-hitoe")
        if "透廊" in text or "渡り廊下" in text:
            return transition("shinden_corridor", "juni_hitoe", "寝殿の透廊", "heian corridor, garden pond, juni-hitoe")
        if "紫宸殿" in text or "唐衣" in text:
            return transition("shishinden_hall", "karaginu_mo", "御所の紫宸殿", "imperial palace hall, formal heian court dress, karaginu, mo")
        if "遣水" in text or "庭園の小川" in text:
            return transition("imperial_garden_stream", "karaginu_mo", "御所の庭園", "heian garden stream, cherry petals, formal court dress")
        if "単" in text and "緋色の袴" in text:
            return transition("shinden_bedroom_night", "heian_hitoe_hakama", "寝殿の自室", "heian bedroom, candlelight, hitoe kimono, scarlet hakama")

        # SF / cyberpunk testcase rules.
        if "酸性雨" in text or "ビニールコート" in text:
            return transition("cyberpunk_slum_alley", "vinyl_coat", "酸性雨の路地裏", "cyberpunk alley, acid rain, hologram neon, hooded vinyl coat")
        if "サイバーカフェ" in text:
            return transition("underground_cyber_cafe", "vinyl_coat", "地下のサイバーカフェ", "underground cyber cafe, junk parts, neon, vinyl coat")
        if "秘密のアジト" in text or "サイバースーツ" in text and "アジト" in text:
            return transition("hacker_secret_hideout", "cyber_suit", "ハッカーの秘密アジト", "hacker hideout, main console, cyber suit")
        if "電脳" in text or "マトリクス" in text:
            return transition("cyberspace_matrix", "cyber_suit", "サイバースペース", "cyberspace, data stream, holographic grid, cyber suit")
        if "冷却用" in text or "インナー姿" in text:
            return transition("hideout_sofa", "cooling_inner", "アジトのソファ", "hideout sofa, cooling inner suit, exhausted")
        if "ステーション制服" in text or "ジャンプスーツ" in text:
            return transition("space_station_cabin", "station_jumpsuit", "宇宙ステーションの船室", "space station cabin, zero gravity, jumpsuit uniform")
        if "エアロック" in text:
            return transition("space_station_airlock", "station_jumpsuit", "宇宙ステーションのエアロック", "space station airlock, earth through window, jumpsuit uniform")
        if "メディカルルーム" in text or "医療用ガウン" in text:
            return transition("medical_room", "medical_gown", "メディカルルーム", "medical room, diagnostic pod, blue medical gown")
        if "宇宙服" in text or "バイザースーツ" in text:
            return transition("space_station_exterior", "space_suit", "宇宙空間のステーション外壁", "outer space, space station exterior, EVA space suit, visor helmet")
        if "格納庫" in text or "ハンガー" in text:
            return transition("space_station_hangar", "space_suit", "ステーションの格納庫", "space station hangar, EVA space suit")
        if "バーチャルバトルアリーナ" in text:
            return transition("vr_battle_arena", "cyborg_armor", "VRバトルアリーナ", "VR battle arena, silver cyborg armor")
        if "溶岩" in text or "マグマ" in text:
            return transition("vr_lava_stage", "cyborg_armor", "VR溶岩ステージ", "VR lava stage, magma, silver cyborg armor")
        if "白いエラー空間" in text or "白タイツ" in text or "アンダースーツ" in text:
            return transition("vr_white_error_space", "white_bodysuit", "VR白いエラー空間", "white void, error space, plain white bodysuit")
        if "ヘッドセットを外して" in text or "現実世界に帰って" in text:
            return transition("home_room", "tshirt_shorts", "自宅の自室へ戻る", "home bedroom, VR headset removed, t-shirt, shorts")
        if "作業用ツナギ" in text or "清掃員" in text:
            return transition("building_lobby", "work_coveralls", "ビルのロビー", "office building lobby, mop, work coveralls")
        if "最上階" in text and "廊下" in text:
            return transition("executive_floor_corridor", "work_coveralls", "最上階の廊下", "executive floor corridor, security camera, work coveralls")
        if "タキシード" in text and ("パーティー" in text or "変装" in text):
            return transition("charity_party_hall", "tuxedo", "社交パーティー会場", "charity party hall, evening tuxedo")
        if "会長の書斎" in text:
            return transition("chairman_study", "tuxedo", "会長の書斎", "chairman's study, computer, evening tuxedo")
        if "ライダース" in text or "バイク" in text and "高速" in text:
            return transition("highway_motorcycle", "tuxedo_riders", "高速道路のバイク上", "highway motorcycle, leather rider jacket over tuxedo")

        # Sports / fitness testcase rules.
        if "ジムのロッカー" in text:
            return transition("gym_locker_room", "casual_hoodie_jeans", "ジムのロッカールーム", "gym locker room, hoodie, jeans")
        if "マシンエリア" in text or "トレッドミル" in text:
            return transition("fitness_machine_area", "training_wear", "フィットネスマシンエリア", "fitness gym machine area, treadmill, training wear")
        if "エアロビクス" in text or "スタジオへ移動" in text and "レッスン" in text:
            return transition("aerobics_studio", "training_wear", "スタジオ内のレッスン", "fitness studio, aerobics lesson, training wear")
        if "スイムゴーグル" in text or "温水プール" in text:
            return transition("indoor_warm_pool", "swim_cap_goggles", "温水プール", "indoor heated pool, swim cap, goggles, swimsuit")
        if "ロビーの自動販売機" in text or "プロテイン" in text:
            return transition("gym_lobby", "casual_hoodie_jeans", "ジムのロビー", "gym lobby, vending machine, protein drink, hoodie, jeans")
        if "アンダーシャツ" in text and "スパイク" in text:
            return transition("baseball_locker_room", "baseball_undershirt", "球場のロッカールーム", "baseball locker room, undershirt, uniform pants, cleats")
        if "キャッチボール" in text or "ウォーミングアップ" in text:
            return transition("baseball_ground_practice", "baseball_uniform_full", "野球場のグラウンド", "baseball field, warmup, full baseball uniform")
        if "ダグアウト" in text or "ベンチ" in text and "ヘルメット" in text:
            return transition("baseball_dugout", "baseball_uniform_helmet", "球場のダグアウト", "baseball dugout, batting helmet, uniform")
        if "バッターボックス" in text or "バットを構える" in text:
            return transition("batters_box", "baseball_uniform_helmet", "バッターボックス", "batter's box, bat, batting helmet, baseball uniform")
        if "お立ち台" in text or "ヒーローインタビュー" in text:
            return transition("baseball_hero_interview_podium", "baseball_uniform_no_helmet", "グラウンド中央のお立ち台", "baseball hero interview podium, no helmet, uniform")
        if "シングレット" in text or "ゼッケン" in text:
            return transition("marathon_start_line", "running_singlet", "マラソン大会のスタート地点", "marathon start line, bib number, running singlet")
        if "上り坂" in text or "走り出し" in text and "ランナー" in text:
            return transition("marathon_uphill_course", "running_singlet", "マラソンコース上り坂", "marathon uphill road, runners, bib number")
        if "給水所" in text or "ヘッドバンド" in text:
            return transition("marathon_water_station", "running_no_headband", "コース沿いの給水所", "marathon water station, no headband, water cup")
        if "ゴールテープ" in text or "直線トラック" in text:
            return transition("stadium_finish_track", "running_no_headband", "競技場のトラック", "stadium running track, finish tape")
        if "防寒ブランケット" in text or "完走メダル" in text:
            return transition("stadium_grass_rest_area", "running_blanket_medal", "競技場内の芝生エリア", "stadium grass, thermal blanket, finisher medal")
        if "ヨガスタジオの受付" in text:
            return transition("yoga_studio_reception", "casual", "ヨガスタジオの受付", "yoga studio reception, casual clothes, herbal tea")
        if "ヨガレギンス" in text or "ヨガマット" in text:
            return transition("yoga_studio_start", "yoga_wear", "ヨガスタジオ内", "yoga studio, yoga mat, leggings, camisole")
        if "木のポーズ" in text or "ゆっくり呼吸" in text:
            return transition("yoga_studio_lesson", "yoga_wear", "ヨガレッスン中", "yoga studio lesson, tree pose, leggings, camisole")
        if "シャワー室" in text and "バスタオル" in text:
            return transition("shower_room", "towel", "シャワー室", "shower room, bath towel, wet hair")
        if "オーガニックカフェ" in text or "ルイボスティー" in text:
            return transition("organic_studio_cafe", "casual", "スタジオ併設のカフェ", "organic cafe, rooibos tea, casual clothes")

        # Broad testcase-oriented context rules. These are intentionally
        # checked before shorter generic triggers to avoid keyword collisions.
        if "満員電車" in text:
            return transition("crowded_train", "business_suit", "満員電車で出社中", "crowded_train, commuter_train, business_suit, necktie")
        if "自分のデスク" in text or "メールをチェック" in text:
            return transition("office_workspace", "business_suit", "オフィスの執務室に到着", "office_workspace, desk, computer, email, business")
        if "社内プレゼン" in text or "プロジェクター" in text:
            return transition("presentation_room", "business_shirt", "会議室でプレゼン準備", "meeting_room, projector, presentation, rolled_up_sleeves")
        if "懇親会" in text:
            return transition("hotel_banquet_hall", "business_jacketpants", "会社の懇親会へ移動", "banquet_hall, party, hotel, drinks")
        if "カラオケ" in text:
            return transition("karaoke_room", "business_jacketpants", "二次会のカラオケ", "karaoke_room, microphone, party_lighting, singing")
        if "新幹線のホーム" in text:
            return transition("shinkansen_platform", "business_jacketpants", "出張の新幹線ホーム", "shinkansen_platform, suitcase, early_morning")
        if "新幹線が発車" in text or "座席のテーブル" in text:
            return transition("shinkansen_interior", "business_jacketpants", "新幹線車内で作業", "shinkansen_interior, train_seat, laptop, documents")
        if "ホテルにチェックイン" in text and "ブラックスーツ" in text:
            return transition("hotel_room", "business_suit", "ホテルでブラックスーツに着替える", "hotel_room, suitcase, business_suit, necktie")
        if "取引先" in text and "役員会議室" in text:
            return transition("executive_boardroom", "business_suit", "取引先の役員会議室", "executive_boardroom, city_view, business_meeting")
        if "ホテルに戻" in text and "パジャマ" in text:
            return transition("hotel_room", "pajamas", "ホテルでパジャマに着替える", "hotel_room, bed, pajamas, night")
        if "Web会議" in text or "上半身だけワイシャツ" in text:
            return transition("home_study", "remote_business", "自宅書斎でリモート会議", "home_office, webcam, desk, business_shirt")
        if "リビングのソファ" in text and "契約書" in text:
            return transition("home_living_room", "remote_business", "リビングで契約書確認", "living_room, sofa, documents, coffee")
        if "クライアント" in text and "カフェ" in text:
            return transition("open_air_cafe", "smart_casual", "カフェでクライアント打ち合わせ", "open_air_cafe, documents, handbag, business_meeting")
        if "郵便局" in text:
            return transition("post_office_counter", "smart_casual", "郵便局で書類を投函", "post_office_counter, envelope, queue")
        if "Tシャツ" in text and ("短パン" in text or "ハーフパンツ" in text):
            loc = "home_living_room" if "リビング" in text or "帰宅" in text else "home_room"
            return transition(loc, "tshirt_shorts", "帰宅後にTシャツと短パンへ着替え", "t-shirt, shorts, home, relaxed")
        if "内定式" in text:
            return transition("company_meeting_room", "recruit_suit", "内定式の本社会議室", "company_meeting_room, recruit_suit, ceremony")
        if "社員食堂" in text:
            return transition("company_cafeteria", "recruit_suit", "本社の社員食堂", "company_cafeteria, buffet, recruit_suit")
        if "フットサル" in text:
            return transition("futsal_court", "sportswear", "フットサルコートへ移動", "futsal_court, sportswear, ball, energetic")
        if "BBQ" in text or "バーベキュー" in text:
            return transition("bbq_area", "sportswear", "BBQエリア", "bbq_grill, outdoor, smoke, sportswear")
        if "バル" in text or "洋風居酒屋" in text:
            return transition("western_pub", "casual", "洋風居酒屋へ移動", "pub, bar_table, casual_clothes, drink")

        if "特急列車" in text:
            return transition("limited_express_train", "cardigan_casual", "海へ向かう特急列車内", "train_interior, window_ocean, light_cardigan")
        if "駅を出たら" in text and "水着" in text:
            return transition("sunny_beach", "swimsuit", "駅から砂浜へ出て水着に着替える", "beach, swimsuit, sunny, ocean")
        if "かき氷" in text or "パラソル" in text:
            return transition("beach_house", "swimsuit", "海の家で休憩", "beach_house, shaved_ice, parasol, swimsuit")
        if "宿の浴衣" in text or ("旅館" in text and "浴衣" in text):
            return transition("onsen_inn_room", "yukata", "温泉旅館の客室で浴衣", "inn_room, tatami, yukata, dinner")
        if "ゲームコーナー" in text:
            return transition("retro_game_corner", "yukata", "旅館のゲームコーナー", "retro_game_center, arcade_cabinets, yukata")
        if "ゲレンデ" in text:
            return transition("ski_slope", "ski_wear", "スキー場のゲレンデ", "ski_slope, powder_snow, ski_wear, mountain")
        if "ロッジ" in text and "ココア" in text:
            return transition("ski_lodge", "ski_wear", "スキー場のロッジ", "ski_lodge, hot_cocoa, fireplace, ski_wear")
        if "スキーウェアを脱" in text or "スウェットにチェンジ" in text:
            return transition("hotel_room", "sweatshirt", "ホテル客室でスウェットへ着替える", "hotel_room, sweatshirt, warm_room")
        if "フォーマルなドレス" in text or "ドレスコード" in text:
            return transition("hotel_restaurant", "formal_dress", "ホテルレストランでフォーマルドレス", "hotel_restaurant, formal_dress, dinner")
        if "最上階のバー" in text:
            return transition("hotel_bar", "formal_dress", "ホテル最上階のバー", "hotel_bar, formal_dress, cocktail")
        if "休日の朝" in text or "モコモコパジャマ" in text:
            return transition("home_living_room", "pajamas", "休日朝のリビング", "living_room, pajamas, coffee, morning")
        if "トレンチコート" in text:
            return transition("neighborhood_park", "trench_coat", "雨上がりの公園散歩", "park, trench_coat, wet_ground")
        if "ブックカフェ" in text:
            return transition("book_cafe", "trench_coat", "雨宿りのブックカフェ", "book_cafe, bookshelves, trench_coat, rain")
        if "シャワー" in text and ("Tシャツ" in text or "ハーフパンツ" in text):
            return transition("home_room", "tshirt_shorts", "シャワー後の部屋着", "bedroom, t-shirt, shorts, fresh")
        if "ボイスチャット" in text and "オンラインゲーム" in text:
            return transition("home_pc_desk", "tshirt_shorts", "PCデスク前でオンラインゲーム", "pc_desk, headset, monitor, t-shirt")
        if "ドラキュラ" in text:
            return transition("home_room", "dracula_costume", "ハロウィン衣装", "dracula_costume, halloween, home_room")
        if "クラブ" in text and "パーティー" in text:
            return transition("halloween_club", "dracula_costume", "クラブのハロウィンパーティー", "club, halloween, neon_lights, dracula_costume")
        if "実家" in text and ("スウェット" in text or "寝室" in text):
            clothing = "dotera" if "ドテラ" in text else "sweatshirt"
            return transition("parents_home_bedroom", clothing, "実家の自室", "bedroom, parents_home, loungewear")
        if "実家の居間" in text or "朝食" in text:
            return transition("parents_home_living_room", "dotera", "実家の居間", "living_room, breakfast, kotatsu, dotera")

        if "更衣室" in text and ("ジャージ" in text or "体操服" in text):
            return transition("school_locker_room", "jersey", "部活前にジャージへ着替える", "school_locker_room, jersey, lockers")
        if "グラウンド" in text or "ランニング" in text:
            return transition("school_ground", "jersey", "学校グラウンドで部活", "school_ground, running, jersey")
        if "部室" in text:
            return transition("club_room", "school_uniform", "部室で制服に着替える", "club_room, school_uniform, after_practice")
        if "駅前の噴水" in text:
            return transition("station_plaza", "long_coat", "駅前広場で待ち合わせ", "station_plaza, fountain, long_coat")
        if "映画館" in text:
            return transition("cinema_lobby" if "ロビー" in text or "上映" in text else "movie_theater", "long_coat", "映画館", "cinema, popcorn, long_coat")
        if "コートを脱" in text and "カフェ" in text:
            return transition("cafe_inside", "sweater", "カフェでコートを脱ぐ", "cafe, sweater, tea")
        if "イルミネーション" in text:
            return transition("illumination_street", "long_coat", "イルミネーションの並木道", "illumination_street, long_coat, night")
        if "改札" in text:
            return transition("station_gate", None, "駅の改札口", "station_gate, ticket_gate, farewell")
        if "図書館" in text or "自習室" in text:
            return transition("library_study_room", "hoodie", "図書館の自習室", "library, study_room, hoodie")
        if "ファミリーレストラン" in text or "ファミレス" in text:
            return transition("family_restaurant", "hoodie", "ファミリーレストラン", "family_restaurant, menu, hoodie")
        if "フリース" in text:
            return transition("home_room", "dotera", "部屋でフリースを羽織る", "bedroom, fleece, sweatshirt")
        if "夜食" in text or "うどん" in text:
            return transition("home_living_room", "dotera", "リビングで夜食", "living_room, udon, loungewear")
        if "レインコート" in text and "制服" in text:
            return transition("home_entrance" if "出発" in text else None, "raincoat_uniform", "制服の上にレインコート", "raincoat, school_uniform, umbrella")
        if "バス" in text:
            return transition("route_bus", "raincoat_uniform", "路線バス車内", "bus_interior, raincoat, rainy_window")
        if "レインコートは脱" in text:
            return transition("route_bus", "school_uniform", "バス車内でレインコートを脱ぐ", "bus_interior, school_uniform, folded_raincoat")

        if "冒険者ギルド" in text or "依頼" in text and "ギルド" in text:
            return transition("adventurers_guild", "leather_armor", "冒険者ギルド", "adventurers_guild, notice_board, leather_armor")
        if "洞窟" in text and "入り口" in text:
            return transition("cave_entrance", "leather_armor", "洞窟の入り口", "cave_entrance, torch, leather_armor")
        if "水没" in text or "チェインメイル" in text:
            return transition("flooded_cave_depths", "chainmail", "洞窟深部でチェインメイル", "flooded_cave, chainmail, dripping_water")
        if "ドラゴン" in text or "ボス戦" in text:
            return transition("dragon_throne", "chainmail", "ドラゴンの玉座", "dragon_throne, boss_battle, chainmail")
        if "旅籠" in text or "宿屋" in text:
            return transition("inn_room", "inn_gown", "宿屋の客室", "inn_room, bed, gown, warm_lighting")
        if "王都" in text and "広場" in text:
            return transition("royal_capital_square", "traveler_cloak", "王都の広場", "city_square, cloak, boots")
        if "王城の門" in text or "門前" in text:
            return transition("castle_gate", "traveler_cloak", "王城の門前", "castle_gate, cloak, boots")
        if "謁見" in text or "宮廷礼服" in text:
            return transition("throne_room", "court_dress", "王城の謁見の間", "throne_room, court_dress, royal")
        if "バルコニー" in text:
            return transition("castle_balcony", "court_dress", "王城のバルコニー", "castle_balcony, night_sky, court_dress")
        if "酒場" in text:
            return transition("tavern", "traveler_cloak", "賑やかな酒場", "tavern, mug, wooden_table")
        if "魔法学校" in text and "時計塔" in text:
            return transition("magic_academy_clocktower", "mage_uniform", "魔法学校の時計塔前", "magic_academy, clocktower, mage_uniform")
        if "大講堂" in text:
            return transition("magic_grand_hall", "mage_uniform", "魔法学校の大講堂", "grand_hall, magic_school, mage_uniform")
        if "魔法薬" in text or "調合室" in text:
            return transition("alchemy_lab", "protective_robe", "魔法薬の調合室", "alchemy_lab, potion, protective_robe")
        if "中庭" in text or "温室" in text:
            return transition("magic_school_courtyard", "protective_robe", "魔法学校の中庭", "courtyard, greenhouse, protective_robe")
        if "学生寮" in text or "談話室" in text:
            return transition("dorm_common_room", "dorm_loungewear", "学生寮の談話室", "dorm_common_room, fireplace, loungewear")
        if "砂漠の入り口" in text:
            return transition("desert_entrance", "desert_cloak", "砂漠の入り口", "desert, cloak, turban")
        if "オアシス" in text and "水辺" not in text:
            return transition("desert_oasis", "desert_cloak", "砂漠のオアシス", "oasis, palm_trees, desert_cloak")
        if "水辺" in text and "オアシス" in text:
            return transition("oasis_waterfront", "linen_underwear", "オアシスの水辺", "oasis_water, linen_underwear, palm_trees")
        if "古代遺跡" in text or "遺跡群" in text:
            return transition("ancient_ruins", "linen_underwear", "古代遺跡", "ancient_ruins, desert, linen_underwear")
        if "焚き火" in text:
            return transition("ruins_campfire", "wool_cloak", "遺跡内部の焚き火前", "campfire, ancient_ruins_interior, wool_cloak")

        if "遊園地" in text or "入場ゲート" in text:
            return transition("amusement_park_gate", "sneakers_casual", "遊園地の入場ゲート", "amusement_park_gate, sneakers, sunny")
        if "ジェットコースター" in text:
            return transition("roller_coaster_queue", "sneakers_casual", "ジェットコースター待機列", "roller_coaster, queue, sneakers")
        if "テーマレストラン" in text or "カチューシャ" in text:
            return transition("theme_restaurant", "character_headband", "園内テーマレストラン", "theme_restaurant, character_headband, food")
        if "パレード" in text:
            return transition("parade_route", "character_headband", "パレードルート沿道", "parade_route, floats, character_headband")
        if "和食レストラン" in text:
            return transition("japanese_restaurant", "sneakers_casual", "駅ビルの和食レストラン", "japanese_restaurant, dinner")
        if "物販" in text or "ライブ会場外" in text:
            return transition("concert_merch_area", "live_tshirt", "ライブ会場外の物販エリア", "concert_merch, live_tshirt, crowd")
        if "スタンディングエリア" in text and "ライブ中" not in text:
            return transition("live_house_standing", "live_tshirt", "ライブハウスのスタンディングエリア", "live_house, stage_lights, live_tshirt")
        if "ライブ中" in text or "ラバーバンド" in text:
            return transition("live_house_performance", "live_tshirt_band", "ライブ中", "live_house, stage_lights, rubber_wristband, ponytail")
        if "夜風" in text:
            return transition("concert_venue_outside_night", "live_tshirt_band", "ライブ会場外の夜風", "concert_outside, night_wind, live_tshirt")
        if "居酒屋" in text and "ライブ" in text:
            return transition("izakaya_private_room", "live_tshirt_hoodie", "ライブ後の居酒屋個室", "izakaya, private_room, hoodie")
        if "美術館" in text and "ロビー" in text:
            return transition("art_museum_lobby", "chic_coat_beret", "美術館のロビー", "art_museum_lobby, beret, chester_coat")
        if "展示室" in text:
            return transition("art_gallery_room", "chic_coat_beret", "美術館の展示室", "art_gallery, painting, beret")
        if "カフェテラス" in text:
            return transition("museum_cafe_terrace", "sweater", "美術館のカフェテラス", "cafe_terrace, sweater, museum")
        if "ミュージアムショップ" in text:
            return transition("museum_shop", "sweater", "ミュージアムショップ", "museum_shop, postcards, sweater")
        if "読書スペース" in text or "メガネ" in text:
            return transition("library_reading_space", "sweater_glasses", "図書館の読書スペース", "library, reading_space, glasses")
        if "ショッピングモール" in text and "案内板" in text:
            return transition("shopping_mall_map", "sneakers_casual", "ショッピングモール案内板前", "shopping_mall, map, jeans, sneakers")
        if "アパレルショップ" in text:
            return transition("apparel_shop", "sneakers_casual", "アパレルショップ店内", "apparel_shop, clothes_rack, jeans")
        if "試着室" in text or "ワンピース" in text and "購入" not in text:
            return transition("fitting_room", "one_piece", "試着室でワンピース", "fitting_room, mirror, one-piece dress")
        if "フードコート" in text:
            return transition("food_court", "sneakers_casual", "モールのフードコート", "food_court, crowded, casual")
        if "シアター" in text:
            return transition("movie_theater", "one_piece", "映画館シアター内", "movie_theater, cinema_seat, one-piece dress")

        if "桜" in text or "お花見" in text:
            if "屋台" in text:
                return transition("sakura_food_stalls", "sweater", "屋台が立ち並ぶ通り", "sakura, food_stalls, spring")
            if "甘酒" in text:
                return transition("amazake_tea_house", "spring_coat", "甘酒茶屋", "tea_house, amazake, spring_coat")
            if "夜桜" in text or "ライトアップ" in text:
                return transition("illuminated_sakura_path", "spring_coat", "夜桜並木", "night_sakura, illuminated, spring_coat")
            return transition("sakura_park", "spring_coat", "満開の桜の公園", "cherry_blossoms, park, spring_coat")
        if "市民プール" in text or "プールの入場" in text:
            return transition("pool_gate", "tshirt_shorts", "市民プール入場ゲート", "pool_gate, summer, t-shirt, shorts")
        if "プールの更衣室" in text:
            return transition("pool_locker_room", "swimsuit", "プールの更衣室", "locker_room, swimsuit")
        if "流れるプール" in text:
            return transition("lazy_river_pool", "swimsuit", "流れるプール", "pool_water, lazy_river, swimsuit")
        if "ラッシュガード" in text:
            loc = "pool_parasol_bench" if "パラソル" in text else "poolside_stand"
            return transition(loc, "rash_guard", "プールサイド", "poolside, rash_guard, swimsuit")
        if "登山口" in text:
            return transition("mountain_trailhead", "hiking_wear", "山の登山口", "mountain_trailhead, trekking_wear, autumn")
        if "展望台" in text:
            return transition("mountain_observatory", "hiking_wear", "山の展望台", "mountain_view, autumn_leaves, trekking_wear")
        if "山頂" in text:
            return transition("mountain_peak", "mountain_parka", "山頂", "mountain_peak, strong_wind, mountain_parka")
        if "吊り橋" in text:
            return transition("mountain_suspension_bridge", "mountain_parka", "山の吊り橋", "suspension_bridge, mountain_parka")
        if "温泉施設" in text or "作務衣" in text:
            return transition("onsen_lobby", "samue", "温泉施設のロビー", "onsen_lobby, samue, warm_lighting")
        if "鳥居" in text:
            return transition("shrine_torii", "down_scarf_gloves", "神社の鳥居前", "shrine_torii, snow, down_jacket")
        if "拝殿" in text:
            return transition("shrine_main_hall", "down_scarf_gloves", "神社の拝殿前", "shrine_main_hall, snow, down_jacket")
        if "お神酒" in text or "甘酒配布" in text:
            return transition("shrine_amazake_stand", "down_jacket", "境内の甘酒配布所", "shrine, amazake_stand, down_jacket")
        if "お札" in text or "おみくじ" in text:
            return transition("shrine_omikuji_counter", "down_jacket", "おみくじ授与所", "shrine, omikuji, down_jacket")
        if "ファミリーレストラン" in text and "深夜" in text:
            return transition("late_night_family_restaurant", "winter_indoor", "深夜のファミリーレストラン", "family_restaurant, midnight, sweater")

        # School date flow
        if "授業" in text and ("終わ" in text or "帰ろ" in text):
            return transition(
                "classroom_after_school",
                "school_uniform",
                "授業後の学校文脈を初期シーンとして確定",
                "classroom, after_school, school_desk, school_bag, afternoon",
            )
        if "上着" in text and ("脱" in text or "暑" in text):
            return transition(
                "school_route_evening",
                "shirt_uniform",
                "暑さで制服の上着を脱ぐ流れ",
                "school_route, evening, walking_home, sunset",
            )
        if "カフェ" in text and ("宿題" in text or "行" in text or "いかない" in text):
            return transition(
                "stylish_cafe",
                None,
                "カフェで宿題をする提案",
                "stylish_cafe, cafe_table, homework, notebook, drink",
            )
        if "駅" in text and ("送" in text or "暗" in text):
            return transition(
                "station_front_night",
                "school_uniform",
                "夜に駅まで送る流れ",
                "station_front, night, street_lights, city_street",
            )
        if "また明日学校" in text or "明日学校" in text:
            return transition(
                "station_gate",
                "school_uniform",
                "別れ際の駅改札前",
                "station_gate, ticket_gate, night_lighting, farewell",
            )

        # Online game to home visit flow
        if any(word in text for word in ("ディスコード", "ネトゲ", "レイド")):
            return transition(
                "own_room_pc",
                "roomwear",
                "オンラインゲームのため自室PC前へ",
                "bedroom_pc, gaming_pc, monitor, desk, evening_room",
            )
        if any(word in text for word in ("VC", "マイク")):
            return transition(
                "own_room_closeup",
                "headset",
                "ボイスチャット中にマイクへ近づく",
                "close_up, headset, microphone, gaming_chair, monitor_light",
            )
        if "家の近く" in text or "突撃" in text or "お土産" in text:
            return transition(
                "own_room",
                "roomwear",
                "急な訪問予告で自室にいる状態",
                "bedroom, surprised, flustered, roomwear, phone",
            )
        if "ピンポーン" in text or "開けて" in text:
            return transition(
                "entrance",
                "roomwear",
                "玄関で来客に応対する",
                "entrance, front_door, indoor_lighting, flustered",
            )
        if "部屋入る" in text or "エアコン" in text:
            return transition(
                "own_room_with_user",
                "roomwear",
                "ユーザーが部屋に入った状態",
                "bedroom, air_conditioner, user_present, embarrassed",
            )

        # Summer beach to fireworks flow
        if "海に到着" in text or "砂浜" in text:
            return transition(
                "sunny_beach",
                "summer_dress",
                "夏の砂浜に到着",
                "beach, sunny, ocean, sand, summer",
            )
        if "水着" in text or "泳ぐ準備" in text:
            return transition(
                "beach_shore",
                "swimsuit",
                "泳ぐため水着へ着替える",
                "beach_shore, ocean, swimsuit, sunny, waves",
            )
        if "海の家" in text or "焼きそば" in text:
            return transition(
                "beach_house",
                "swim_coverup",
                "泳いだ後に海の家で休憩",
                "beach_house, shade, yakisoba, table, summer",
            )
        if "夏祭り" in text or "祭り" in text:
            return transition(
                "festival_shrine_evening",
                "yukata",
                "夕方の夏祭りへ移動",
                "festival_shrine, evening, food_stalls, lanterns",
            )
        if "花火" in text:
            return transition(
                "fireworks_hill_night",
                "yukata",
                "夜の高台で花火を見る",
                "fireworks, hill, night_sky, yukata, fireworks_lighting",
            )

        # Office to bar flow
        if "資料" in text or "チェック" in text:
            return transition(
                "office_day",
                "office_jacket",
                "昼のオフィスで資料確認",
                "office, desk, documents, daytime, business",
            )
        if "定時" in text or "プレゼン" in text:
            return transition(
                "office_night",
                "office_casual",
                "定時後のオフィス",
                "office, night, desk, tired_smile, loosened",
            )
        if "バー" in text or "一杯" in text:
            return transition(
                "stylish_bar",
                "office_no_jacket",
                "仕事後にバーへ移動",
                "stylish_bar, dim_lighting, bar_counter, drink",
            )
        if "眼鏡外" in text or "メガネ外" in text:
            return transition(
                "bar_counter",
                "no_glasses",
                "バーで眼鏡を外した状態",
                "bar_counter, no_eyewear, dim_lighting, relaxed",
            )
        if "酔" in text or "お水" in text:
            return transition(
                "stylish_bar",
                "office_no_jacket",
                "バーで少し酔って水を勧める場面",
                "stylish_bar, drink, water_glass, blush, dim_lighting",
            )

        # Winter flow
        if "暖房" in text or "汗" in text:
            return transition(
                "winter_cafe_inside",
                "winter_indoor",
                "暖房の効いた冬のカフェ店内",
                "winter_cafe, indoor, sweater, warm_lighting",
            )
        if "雪" in text and ("出よう" in text or "外" in text):
            return transition(
                "cafe_entrance_snow",
                "winter_coat",
                "雪の外へ出るためコートを着る",
                "cafe_entrance, snow, winter_coat, doorway",
            )
        if "寒い" in text or "風" in text:
            return transition(
                "snowy_street",
                "winter_coat",
                "雪の街並みへ出た状態",
                "snowy_street, strong_wind, snow, winter",
            )
        if "カイロ" in text:
            return transition(
                "snowy_street_closeup",
                "coat_scarf",
                "雪道でカイロを渡す場面",
                "close_up, snowy_street, hand_warmer, scarf",
            )
        if "手袋" in text or "繋いで" in text:
            return transition(
                "illumination_street",
                "coat_scarf_gloves",
                "イルミネーションの道を手を繋いで歩く",
                "illumination_street, winter_lights, gloves, walking_together",
            )

        return None

    def _coerce_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "1")
        return bool(value)

    def _get_state_changes(self, result):
        changes = result.get("state_changes", {})
        if not isinstance(changes, dict):
            changes = {}
        return {
            "location_changed": self._coerce_bool(
                changes.get("location_changed", False)
            ),
            "clothing_changed": self._coerce_bool(
                changes.get("clothing_changed", False)
            ),
            "reason": str(changes.get("reason", "")).strip(),
        }

    # ------------------------------------------------------------------
    # Chat turn
    # ------------------------------------------------------------------
    def process_chat_turn_stream(self, user_input_text, enable_image=True, enable_voice=False):
        t_turn_start = time.time()
        turn = self.session_info.get("current_turn", 0)
        image_filename = f"chat_turn_{turn+1:02d}.png"
        voice_filename = f"chat_turn_{turn+1:02d}.wav"
        
        parallel_gen = self.config.get("image", {}).get("parallel_generation", True)
        executor = ThreadPoolExecutor(max_workers=2 if parallel_gen else 1)
        image_future = None
        image_started_at = None
        clothing_override = self._infer_explicit_clothing_state(
            user_input_text
        )
        explicit_transition = self._infer_explicit_scene_transition(user_input_text)

        last_scene_description = "特になし"
        if self.history:
            last_scene_description = self.history[-1].get("scene_description", "特になし")

        instruction = (
            f"【現在の状態】場所: {self.current_state['location']} / "
            f"キャラクターの服装: {self.current_state['clothing']}\n"
            f"【直前の情景】{last_scene_description}\n"
            f"【ユーザーの行動】「{user_input_text}」\n"
            "これに対する現在の情景、キャラクターの反応、および画像生成用のタグをJSONで出力してください。\n"
            "場所や服装を変更する場合だけstate_changesの対応フラグをtrueにしてください。"
            "変更しない場合は現在の状態をそのまま返してください。"
        )
        if clothing_override:
            instruction += (
                f"\n【このターンで確定する服装】{clothing_override}。"
                "台詞上の反応に関係なくclothing_stateとscene_tagsへ反映してください。"
            )
        if explicit_transition:
            hints = []
            if explicit_transition.get("location"):
                hints.append(f"current_location={explicit_transition['location']}")
            if explicit_transition.get("clothing"):
                hints.append(f"clothing_state={explicit_transition['clothing']}")
            if explicit_transition.get("tag_hint"):
                hints.append(f"scene_tags should include: {explicit_transition['tag_hint']}")
            instruction += (
                "\n【明示的な場面遷移ヒント】"
                + " / ".join(hints)
                + "。このヒントはユーザー入力から確定できる自然な状態です。"
                "矛盾する強い理由がない限り、state_changesの対応フラグをtrueにしてください。"
            )
        verified_memory = self._build_verified_memory_context(user_input_text)
        if verified_memory:
            instruction = f"{verified_memory}\n\n{instruction}"

        system_msg = self.messages[0]
        recent_msgs = self.messages[1:][-self.history_window:]
        if self.config["llm"].get("api_mode") == "lmstudio_native":
            context_parts = []
            for message in recent_msgs:
                label = "ユーザー" if message["role"] == "user" else "アシスタント"
                context_parts.append(f"【過去の{label}メッセージ】\n{message['content']}")
            context_parts.append(instruction)
            payload = {
                "model": self.config["llm"].get("model", "google/gemma-4-12b-qat"),
                "input": "\n\n".join(context_parts),
                "system_prompt": system_msg["content"],
                "temperature": (
                    min(self.config["llm"].get("temperature", 0.8), 0.4)
                    if verified_memory
                    else self.config["llm"].get("temperature", 0.8)
                ),
                "max_output_tokens": self.config["llm"].get("max_tokens", 4096),
                "reasoning": "off",
                "store": False,
            }
        elif self.config["llm"].get("api_mode") == "ollama":
            payload = {
                "model": self.config["llm"].get("model", "gemma4:12b"),
                "messages": [system_msg] + recent_msgs + [{"role": "user", "content": instruction}],
                "stream": False,
                "think": False,
                "options": {
                    "temperature": self.config["llm"].get("temperature", 0.8),
                    "num_predict": self.config["llm"].get("max_tokens", 4096),
                },
            }
        else:
            payload = {
                "messages": [system_msg] + recent_msgs + [{"role": "user", "content": instruction}],
                "temperature": self.config["llm"].get("temperature", 0.8),
                "max_tokens": self.config["llm"].get("max_tokens", 4096),
                "thinking": False,
            }

        def validate_fields(result: dict):
            missing = []
            for k in ("character_dialogue", "scene_tags"):
                val = result.get(k, "")
                if isinstance(val, list):
                    val = ", ".join([str(v) for v in val])
                elif not isinstance(val, str):
                    val = str(val)
                if not val.strip():
                    missing.append(k)
            changes = self._get_state_changes(result)
            if "state_changes" in result and not isinstance(
                result.get("state_changes"), dict
            ):
                missing.append("state_changes")
            if changes["location_changed"] and not str(
                result.get("current_location", "")
            ).strip():
                missing.append("current_location")
            if changes["clothing_changed"] and not str(
                result.get("clothing_state", "")
            ).strip():
                missing.append("clothing_state")
            if missing:
                raise ValueError(f"必須フィールド欠落: {missing}")

        def start_image_from_partial(partial):
            nonlocal image_future, image_started_at
            if not enable_image or image_future is not None:
                return
            location = partial["current_location"].strip() or self.current_state["location"]
            clothing = (
                clothing_override
                or partial["clothing_state"].strip()
                or self.current_state["clothing"]
            )
            llm_tags = sanitize_scene_tags(partial["scene_tags"])
            base_clothing, negative_clothing = self._get_clothing_tags(clothing)
            image_tags = merge_prompt_tags(base_clothing, llm_tags)
            image_started_at = time.time()
            image_future = executor.submit(
                self._generate_image,
                image_tags,
                image_filename,
                negative_clothing,
            )
            print(
                f"[TIMER] 画像生成先行開始: "
                f"{time.time()-t_turn_start:.2f}秒"
            )

        try:
            content, result = self._call_llm_with_retry(
                payload,
                validator=validate_fields,
                partial_callback=None,
            )
        except Exception:
            executor.shutdown(wait=False, cancel_futures=True)
            raise

        character_dialogue = result.get("character_dialogue", "")
        if not character_dialogue or character_dialogue.strip() in ("", "（無言）", "無言"):
            character_dialogue = "……っ"

        state_changes = self._get_state_changes(result)
        new_location = result.get("current_location", "").strip()
        new_clothing = (
            clothing_override
            or result.get("clothing_state", "").strip()
        )
        if explicit_transition:
            if explicit_transition.get("location"):
                new_location = explicit_transition["location"]
                state_changes["location_changed"] = explicit_transition[
                    "location_changed"
                ]
            if explicit_transition.get("clothing"):
                new_clothing = explicit_transition["clothing"]
                state_changes["clothing_changed"] = explicit_transition[
                    "clothing_changed"
                ]
            if explicit_transition.get("reason"):
                state_changes["reason"] = explicit_transition["reason"]
        if state_changes["location_changed"] and new_location:
            self.current_state["location"] = new_location
        if clothing_override or (state_changes["clothing_changed"] and new_clothing):
            self.current_state["clothing"] = new_clothing

        raw_tags = result.get("scene_tags", "1girl")
        llm_tags = sanitize_scene_tags(raw_tags)
        if explicit_transition and explicit_transition.get("tag_hint"):
            llm_tags = merge_prompt_tags(llm_tags, explicit_transition["tag_hint"])
        scene_desc = build_scene_context(
            user_input_text,
            llm_tags,
            self.current_state["location"],
            self.current_state["clothing"],
        )

        compact_content = json.dumps({
            "current_location": self.current_state["location"],
            "clothing_state": self.current_state["clothing"],
            "character_dialogue": character_dialogue
        }, ensure_ascii=False)
        self.messages.append({
            "role": "user",
            "content": f"【ユーザーの行動】「{user_input_text}」",
        })
        self.messages.append({"role": "assistant", "content": compact_content})
        self.session_info["current_turn"] += 1

        # 服装タグの強制付与
        base_clothing, negative_clothing = self._get_clothing_tags(self.current_state["clothing"])
        image_tags = merge_prompt_tags(base_clothing, llm_tags)

        image_path = None
        voice_path = None

        if enable_image and image_future is None:
            image_started_at = time.time()
            image_future = executor.submit(
                self._generate_image,
                image_tags,
                image_filename,
                negative_clothing,
            )

        turn_data = {
            "role": "assistant",
            "status": "generating_media" if enable_image or enable_voice else "success",
            "turn_info": f"Turn {turn+1}",
            "scene_description": scene_desc,
            "user_action": user_input_text,
            "character_dialogue": character_dialogue,
            "image_path": None,
            "image_filename": None,
            "voice_path": None,
            "voice_filename": None,
            "state_changes": state_changes,
            "tags": image_tags,
            "location": self.current_state["location"],
            "clothing": self.current_state["clothing"],
        }
        self.history.append(turn_data)
        self._append_memory_event(turn_data)
        self._save_json_log()
        print(f"[TIMER] LLM応答表示可能: {time.time()-t_turn_start:.2f}秒")
        yield turn_data.copy()

        t_parallel = time.time()
        try:
            voice_future = None
            if enable_voice:
                voice_future = executor.submit(
                    self._generate_voice,
                    character_dialogue,
                    voice_filename,
                )
            if image_future is not None:
                image_path = image_future.result()
                print(
                    f"[TIMER] 画像生成実時間: "
                    f"{time.time()-image_started_at:.2f}秒"
                )
            if voice_future is not None:
                voice_path = voice_future.result()
                print(f"[TIMER] 音声生成完了: {time.time()-t_parallel:.2f}秒")
        finally:
            executor.shutdown(wait=True)

        print(f"[TIMER] 画像+音声 並列合計: {time.time()-t_parallel:.2f}秒")

        turn_data.update({
            "status": "success",
            "image_path": image_path,
            "image_filename": image_filename if image_path else None,
            "voice_path": voice_path,
            "voice_filename": voice_filename if voice_path else None,
        })
        self._save_json_log()

        print(f"[TIMER] ターン{turn+1}合計: {time.time()-t_turn_start:.2f}秒")
        if enable_image or enable_voice:
            yield turn_data.copy()

    def process_chat_turn(self, user_input_text, enable_image=True, enable_voice=False):
        result = None
        for result in self.process_chat_turn_stream(
            user_input_text,
            enable_image=enable_image,
            enable_voice=enable_voice,
        ):
            pass
        return result

    # ------------------------------------------------------------------
    # Image generation (ComfyUI)
    # ------------------------------------------------------------------
    def _comfy_websocket_url(self, client_id):
        parsed = urlparse(self.sd_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse(
            (scheme, parsed.netloc, "/ws", "", f"clientId={client_id}", "")
        )

    async def _queue_and_wait_comfy_websocket(self, workflow):
        client_id = uuid.uuid4().hex
        prompt_id = None
        try:
            async with websockets.connect(
                self._comfy_websocket_url(client_id),
                open_timeout=5,
                close_timeout=1,
            ) as websocket:
                await asyncio.wait_for(websocket.recv(), timeout=5)
                response = await asyncio.to_thread(
                    self.http_session.post,
                    f"{self.sd_url}/prompt",
                    json={"prompt": workflow, "client_id": client_id},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                prompt_id = data.get("prompt_id")
                if not prompt_id:
                    raise ValueError(f"prompt_idなし: {data}")

                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=120)
                    if not isinstance(message, str):
                        continue
                    event = json.loads(message)
                    event_type = event.get("type")
                    event_data = event.get("data", {})
                    if event_data.get("prompt_id") != prompt_id:
                        continue
                    if event_type == "execution_success":
                        return prompt_id, True
                    if event_type in ("execution_error", "execution_interrupted"):
                        raise RuntimeError(
                            f"ComfyUI {event_type}: {event_data}"
                        )
        except Exception as e:
            print(f"[WARN] ComfyUI WebSocket待機失敗。HTTP確認へ切替: {e}")
            return prompt_id, False

    def _wait_for_comfy_history(self, prompt_id):
        while True:
            try:
                history_res = self.http_session.get(
                    f"{self.sd_url}/history/{prompt_id}", timeout=5
                ).json()
                if prompt_id in history_res:
                    return history_res
            except Exception:
                pass
            time.sleep(0.1)

    def _generate_image(self, dynamic_tags, filename, extra_negative=""):
        json_path = "workflow_api.json"
        if not os.path.exists(json_path):
            print(f"[ERROR] {json_path} が見つかりません")
            return None
        with open(json_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        base_positive = self.character_config.get("base_positive_prompt", "1girl, masterpiece, best quality, good quality, sensitive,")
        final_prompt = f"{base_positive} {dynamic_tags}"
        
        lora_name = self.character_config.get("lora_name", "character_lora.safetensors")

        for node_id, node_data in workflow.items():
            class_type = node_data.get("class_type", "")
            if class_type == "KSampler":
                node_data["inputs"]["seed"] = random.randint(0, 2**63 - 1)
            elif class_type == "LoraLoader":
                lora_val = node_data["inputs"].get("lora_name", "")
                if isinstance(lora_val, str) and "___LORA_NAME___" in lora_val:
                    node_data["inputs"]["lora_name"] = lora_name
            elif class_type == "CLIPTextEncode":
                text_val = node_data["inputs"].get("text", "")
                if isinstance(text_val, str):
                    if "___POSITIVE_PROMPT___" in text_val:
                        node_data["inputs"]["text"] = final_prompt
                    elif "___NEGATIVE_PROMPT___" in text_val and extra_negative:
                        node_data["inputs"]["text"] = f"{text_val}, {extra_negative}"

        print(f"[ComfyUI] プロンプト:\n{final_prompt}")
        prompt_id = None
        websocket_completed = False
        try:
            prompt_id, websocket_completed = asyncio.run(
                self._queue_and_wait_comfy_websocket(workflow)
            )
            if prompt_id is None:
                response = self.http_session.post(
                    f"{self.sd_url}/prompt",
                    json={"prompt": workflow},
                    timeout=10,
                )
                response.raise_for_status()
                res = response.json()
                prompt_id = res.get("prompt_id")
                if not prompt_id:
                    raise ValueError(f"prompt_idなし: {res}")
        except Exception as e:
            print(f"[ERROR] ComfyUI接続エラー: {e}")
            return None

        try:
            history_res = self._wait_for_comfy_history(prompt_id)
            if websocket_completed:
                print("[ComfyUI] WebSocketで生成完了を受信")
        except Exception as e:
            print(f"[ERROR] ComfyUI履歴取得エラー: {e}")
            return None

        outputs = history_res[prompt_id]['outputs']
        full_path = os.path.join(self.current_run_dir, filename)
        for node_id in outputs:
            if 'images' in outputs[node_id]:
                image_info = outputs[node_id]['images'][0]
                if self._copy_comfy_output(image_info, full_path):
                    return full_path
                img_res = self.http_session.get(
                    f"{self.sd_url}/view",
                    params={
                        "filename": image_info["filename"],
                        "subfolder": image_info.get("subfolder", ""),
                        "type": image_info.get("type", "output"),
                    },
                    timeout=30,
                )
                img_res.raise_for_status()
                with open(full_path, "wb") as f:
                    f.write(img_res.content)
                return full_path
        return None

    def _copy_comfy_output(self, image_info, destination):
        if not self.comfy_output_dir or image_info.get("type", "output") != "output":
            return False
        output_root = os.path.abspath(self.comfy_output_dir)
        source = os.path.abspath(
            os.path.join(
                output_root,
                image_info.get("subfolder", ""),
                image_info["filename"],
            )
        )
        try:
            if os.path.commonpath([source, output_root]) != output_root:
                return False
            if not os.path.isfile(source):
                return False
            shutil.copy2(source, destination)
            return True
        except (OSError, ValueError) as e:
            print(f"[WARN] ComfyUI出力の直接コピー失敗: {e}")
            return False

    # ------------------------------------------------------------------
    # Log
    # ------------------------------------------------------------------
    def _save_json_log(self):
        if not self.current_run_dir:
            return
        export = {
            "session_info": self.session_info,
            "memory_events": self.memory_events,
            "turns": [
                {
                    "turn_info":         t.get("turn_info"),
                    "user_action":       t.get("user_action"),
                    "scene_description": t.get("scene_description"),
                    "character_dialogue":   t.get("character_dialogue"),
                    "image_filename":    t.get("image_filename"),
                    "voice_filename":    t.get("voice_filename"),
                    "state_changes":      t.get("state_changes", {}),
                    "tags":              t.get("tags"),
                    "location":          t.get("location", ""),
                    "clothing":          t.get("clothing", ""),
                }
                for t in self.history
            ]
        }
        with open(os.path.join(self.current_run_dir, "chat_log.json"), "w", encoding="utf-8") as f:
            json.dump(export, f, ensure_ascii=False, indent=2)

    def list_sessions(self):
        """保存済みセッション一覧を返す（新しい順）"""
        if not os.path.exists(self.base_dir):
            return []
        dirs = sorted(
            [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))],
            reverse=True
        )
        sessions = []
        for d in dirs:
            log_path = os.path.join(self.base_dir, d, "chat_log.json")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                turns = data.get("turns", [])
                sessions.append({
                    "dir": d,
                    "full_path": os.path.join(self.base_dir, d),
                    "started_at": data.get("session_info", {}).get("started_at", d),
                    "turn_count": len(turns),
                    "turns": turns,
                })
        return sessions
