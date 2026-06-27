import asyncio
import requests
import json
import os
import re
import time
import uuid
from datetime import datetime
import random
from scene_state.normalizer import DynamicSceneRegistry, normalize_dynamic_candidate
from tag_utils import merge_prompt_tags
from urllib.parse import urlparse, urlunparse
import websockets
from gradio_client import Client, handle_file
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
        import os
        os.makedirs(self.base_dir, exist_ok=True)
        
        voice_path = self.character_config.get("prompts", {}).get("voice_examples", "./prompts/voice_examples.md")
        self.voice_examples = self._load_voice_examples(voice_path)
        
        self.tts_client = None
        self._tts_initialized = False
        self.scene_state_config = self.config.get("scene_state", {})
        registry_path = self.scene_state_config.get("registry_path", "scene_state/dynamic_registry.json")
        self.dynamic_registry = DynamicSceneRegistry(registry_path)
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
            
            ref_wav = self.config["tts"].get("reference_wav")
            uploaded_audio = handle_file(ref_wav) if ref_wav and os.path.exists(ref_wav) else None

            result = self.tts_client.predict(
                checkpoint=self.tts_checkpoint,
                model_device="cuda", model_precision="bf16",
                codec_device="cuda", codec_precision="bf16",
                text=text, uploaded_audio=uploaded_audio,
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

        return None


    def _infer_dynamic_scene_transition(self, user_input):
        if not self.scene_state_config.get("dynamic_enabled", True):
            return None
        try:
            _, raw = self._call_llm_with_retry(
                self._state_inference_payload(user_input),
                max_retries=1,
                retry_delay=0,
            )
            candidate = normalize_dynamic_candidate(raw, self.current_state)
        except Exception as exc:
            print(f"[STATE] dynamic inference skipped: {exc}")
            return None
        if not candidate:
            return None

        threshold = float(self.scene_state_config.get("confidence_threshold", 0.72))
        if candidate.get("location") and candidate.get("location_confidence", 0) >= threshold:
            reg = candidate["registry"]["location"]
            self.dynamic_registry.register(
                "locations",
                reg["key"],
                reg.get("label_ja", ""),
                reg.get("image_tags", ""),
                reg.get("aliases", []),
            )
        else:
            candidate["location"] = None
            candidate["location_changed"] = False
        if candidate.get("clothing") and candidate.get("clothing_confidence", 0) >= threshold:
            reg = candidate["registry"]["clothing"]
            self.dynamic_registry.register(
                "clothing",
                reg["key"],
                reg.get("label_ja", ""),
                reg.get("image_tags", ""),
                reg.get("aliases", []),
            )
        else:
            candidate["clothing"] = None
            candidate["clothing_changed"] = False
        if not candidate.get("location") and not candidate.get("clothing") and not candidate.get("tag_hint"):
            return None
        return candidate

    def _registry_transition_candidate(self, user_input):
        matches = self.dynamic_registry.match_text(user_input)
        current_location = self.current_state.get("location", "")
        current_clothing = self.current_state.get("clothing", "")
        location = None
        clothing = None
        tags = []
        if matches["locations"]:
            _, location, item = matches["locations"][0]
            tags.append(item.get("image_tags", ""))
        if matches["clothing"]:
            _, clothing, item = matches["clothing"][0]
            tags.append(item.get("image_tags", ""))
        if not location and not clothing:
            return None
        return {
            "location": location if location != current_location else None,
            "clothing": clothing if clothing != current_clothing else None,
            "location_changed": bool(location and location != current_location),
            "clothing_changed": bool(clothing and clothing != current_clothing),
            "reason": "dynamic registry match",
            "tag_hint": merge_prompt_tags(*tags),
            "location_confidence": 0.92 if location else 0.0,
            "clothing_confidence": 0.92 if clothing else 0.0,
            "source": "registry",
        }

    def _is_generic_rule_candidate(self, candidate):
        if not candidate:
            return True
        generic_locations = {
            "castle_balcony", "amusement_park_gate", "parade_route", "movie_theater",
            "fitting_room", "home_room", "kitchen", "route_bus", "station_gate",
            "stylish_bar", "cafe_inside", "snowy_street", "illumination_street",
            "cyberpunk_alleyway",
        }
        if candidate.get("location") in generic_locations:
            return True
        tag_hint = str(candidate.get("tag_hint", ""))
        return len(tag_hint) < 20

    def _needs_dynamic_inference(self, user_input, rule_candidate, registry_candidate):
        if not self.scene_state_config.get("dynamic_enabled", True):
            return False
        if rule_candidate and not self._is_generic_rule_candidate(rule_candidate):
            return False
        if registry_candidate and not self._is_generic_rule_candidate(registry_candidate):
            return False
        text = str(user_input)
        change_markers = (
            "着替", "脱", "羽織", "かぶ", "被", "手袋", "マスク", "ヘルメット",
            "ベール", "ポンチョ", "合羽", "エプロン", "コート", "パーカー",
            "移動", "入って", "出て", "戻", "向か", "到着", "ロビー", "工房",
            "ランドリー", "屋上", "プラネタリウム", "スタジオ",
        )
        return any(marker in text for marker in change_markers)

    def _resolve_scene_transition(self, rule_candidate, dynamic_candidate):
        if not rule_candidate:
            return dynamic_candidate
        if not dynamic_candidate:
            rule_candidate["source"] = rule_candidate.get("source", "rule")
            return rule_candidate

        generic_locations = {
            "castle_balcony", "amusement_park_gate", "parade_route", "movie_theater",
            "fitting_room", "home_room", "kitchen", "route_bus", "station_gate",
            "stylish_bar", "cafe_inside", "snowy_street", "illumination_street",
        }
        high_dynamic = (
            dynamic_candidate.get("location_confidence", 0) >= 0.88
            or dynamic_candidate.get("clothing_confidence", 0) >= 0.88
        )
        rule_location = rule_candidate.get("location")
        if high_dynamic and (rule_location in generic_locations):
            return dynamic_candidate

        merged = dict(rule_candidate)
        merged["source"] = "rule+dynamic"
        if (
            rule_location in generic_locations
            and dynamic_candidate
            and not dynamic_candidate.get("location")
            and dynamic_candidate.get("clothing_confidence", 0) >= 0.85
        ):
            merged["location"] = None
            merged["location_changed"] = False
        if not merged.get("location") and dynamic_candidate.get("location"):
            merged["location"] = dynamic_candidate["location"]
            merged["location_changed"] = dynamic_candidate["location_changed"]
        if not merged.get("clothing") and dynamic_candidate.get("clothing"):
            merged["clothing"] = dynamic_candidate["clothing"]
            merged["clothing_changed"] = dynamic_candidate["clothing_changed"]
        if dynamic_candidate.get("tag_hint"):
            merged["tag_hint"] = merge_prompt_tags(
                merged.get("tag_hint", ""), dynamic_candidate["tag_hint"]
            )
        merged["location_confidence"] = dynamic_candidate.get("location_confidence", 0)
        merged["clothing_confidence"] = dynamic_candidate.get("clothing_confidence", 0)
        if not merged.get("reason"):
            merged["reason"] = dynamic_candidate.get("reason", "")
        return merged

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
        rule_transition = self._infer_explicit_scene_transition(user_input_text)
        registry_transition = self._registry_transition_candidate(user_input_text)
        dynamic_transition = None
        if self._needs_dynamic_inference(
            user_input_text, rule_transition, registry_transition
        ):
            dynamic_transition = self._infer_dynamic_scene_transition(user_input_text)
        explicit_transition = self._resolve_scene_transition(
            self._resolve_scene_transition(rule_transition, registry_transition),
            dynamic_transition,
        )

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
