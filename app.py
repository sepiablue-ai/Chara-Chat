import gradio as gr
from chat_engine import ChatEngine
import os
import sys
from pathlib import Path
from urllib.parse import quote

# Windows環境での文字化け対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def load_prompts():
    """engine.config からプロンプトのパスを取得して読み込む"""
    char_config = engine.character_config
    prompt_paths = char_config.get("prompts", {})
    
    defaults = {
        "character_setting": "以下設定でロールプレイして。名前はAI助手。",
        "main_director": "{character_setting}\nあなたは優秀なAIディレクターです。",
    }
    
    result = {}
    # character_setting
    path = prompt_paths.get("character_setting", "prompts/character_setting.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            result["character_setting"] = f.read()
    else:
        result["character_setting"] = defaults["character_setting"]
        
    # main_director
    path = prompt_paths.get("main_director", "prompts/main_ai_director.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            result["main_director"] = f.read()
    else:
        result["main_director"] = defaults["main_director"]
        
    return result

# グローバルエンジン
engine = ChatEngine()

def init_engine():
    prompts = load_prompts()
    engine.initialize_session(
        prompts["character_setting"],
        prompts["main_director"]
    )
    return [], render_html([])

# --------------------------------------------------
# ユーティリティ: Gradioの許可済みファイル配信URLを生成
# --------------------------------------------------
def get_media_src(filepath):
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        resolved = Path(filepath).resolve()
        memories_root = Path(engine.base_dir).resolve()
        resolved.relative_to(memories_root)
        encoded_path = quote(resolved.as_posix(), safe="/:")
        return f"/gradio_api/file={encoded_path}"
    except Exception as e:
        print(f"メディアURL生成エラー: {e}")
        return None

# --------------------------------------------------
# HTMLレンダラー
# --------------------------------------------------
def render_html(turns):
    if not turns:
        return """
        <div style="
            display:flex; flex-direction:column; align-items:center;
            justify-content:center; height:300px; gap:16px;
        ">
            <div style="font-size:52px;">💭</div>
            <div style="font-size:15px; color:var(--body-text-color); opacity:0.7; font-family:'Noto Sans JP',sans-serif;">
                会話を始めてみてね！
            </div>
        </div>
        """

    html_parts = []
    for turn in turns:
        role = turn.get("role")
        if role == "user":
            text = turn.get("text", "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            html_parts.append(f"""
            <div style="display:flex; justify-content:flex-end; margin:10px 0;">
                <div style="
                    background:linear-gradient(135deg,#7c3aed,#6d28d9);
                    color:white; border-radius:18px 18px 4px 18px;
                    padding:12px 18px; max-width:72%; font-size:15px;
                    line-height:1.7; box-shadow:0 4px 20px rgba(124,58,237,0.3);
                    font-family:'Noto Sans JP',sans-serif;
                ">{text}</div>
            </div>
            """)
        elif role == "character":
            text = turn.get("text", "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            img_path = turn.get("image_path")
            voice_path = turn.get("voice_path")
            media_pending = turn.get("media_pending", False)
            media_error = turn.get("media_error")

            # 画像はGradioのファイル配信を利用し、HTMLへのBase64埋め込みを避ける
            img_html = ""
            image_src = get_media_src(img_path)
            if image_src:
                img_html = f"""
                <div style="margin-top:10px;">
                    <img src="{image_src}" loading="lazy" style="
                        max-width:300px; width:100%; border-radius:12px;
                        box-shadow:0 4px 20px var(--chat-shadow);
                        transition:transform 0.3s ease;
                        cursor:pointer;
                    "
                    onmouseover="this.style.transform='scale(1.03)'"
                    onmouseout="this.style.transform='scale(1)'"
                    />
                </div>
                """

            # 音声も再生時にだけ取得する
            voice_html = ""
            voice_src = get_media_src(voice_path)
            if voice_src:
                # Safari対策: 辞書のメモリIDを使って、タグごとに一意のIDを付与
                uid = id(turn) 
                
                # Safari対策: preload="none" で複数音声の同時ロードによるクラッシュを防ぐ
                voice_html = f"""
                <div style="margin-top:10px; width:260px; flex-shrink:0;">
                    <audio id="audio_{uid}" controls preload="none" src="{voice_src}" style="
                        width:100%; height:44px; display:block;
                        border-radius:20px; outline:none;
                        accent-color:#db2777;
                    "></audio>
                </div>
                """

            media_status_html = ""
            if media_pending:
                media_status_html = """
                <div style="margin-top:10px; font-size:12px; opacity:0.65;">
                    画像・音声を生成中...
                </div>
                """
            elif media_error:
                media_status_html = f"""
                <div style="margin-top:10px; font-size:12px; color:#dc2626;">
                    メディア生成エラー: {media_error}
                </div>
                """

            html_parts.append(f"""
            <div style="display:flex; justify-content:flex-start; align-items:flex-start; gap:10px; margin:10px 0;">
                <div style="
                    width:38px; height:38px; flex-shrink:0;
                    background:linear-gradient(135deg,#db2777,#f43f5e);
                    border-radius:50%; display:flex; align-items:center;
                    justify-content:center; font-size:20px;
                    box-shadow:0 2px 10px rgba(219,39,119,0.4);
                    margin-top:4px;
                ">✨</div>
                <div style="max-width:78%;">
                    <div style="font-size:11px; color:#db2777; font-weight:700;
                        margin-bottom:5px; letter-spacing:0.5px; font-family:'Noto Sans JP',sans-serif;">
                        {engine.character_config.get("display_name", "AI Character")}
                    </div>
                    <div style="
                        background: var(--chat-bg);
                        border: 1px solid var(--chat-border);
                        border-radius: 4px 18px 18px 18px;
                        padding: 12px 16px; font-size: 15px; line-height: 1.7;
                        color: var(--body-text-color);
                        font-family: 'Noto Sans JP', sans-serif;
                        box-shadow: 0 2px 12px var(--chat-shadow);
                        backdrop-filter: blur(6px);
                    ">{text}</div>
                    {media_status_html}
                    {img_html}
                    {voice_html}
                </div>
            </div>
            """)

    scroll_js = """
    <script>
        (function() {
            var el = document.getElementById('chat-scroll-area');
            if (el) { el.scrollTop = el.scrollHeight; }
        })();
    </script>
    """

    return f"""
    <div id="chat-scroll-area" style="
        height:calc(100vh - 260px); min-height:400px;
        overflow-y:auto; padding:10px 6px;
        scrollbar-width:thin; scrollbar-color:var(--border-color-primary) transparent;
    ">
        {''.join(html_parts)}
        {scroll_js}
    </div>
    """

# --------------------------------------------------
# セッション読み込み用関数
# --------------------------------------------------
def load_chat_history(session_dir):
    if not session_dir:
        return [], render_html([])
    
    prompts = load_prompts()
    try:
        # エンジンに状態を復元させる
        history = engine.load_session(
            session_dir,
            prompts["character_setting"],
            prompts["main_director"]
        )
        
        # Gradio UI用の表示データ（turns）に変換
        turns = []
        for t in history:
            turns.append({"role": "user", "text": t["user_action"]})
            turns.append({
                "role": "character",
                "text": t["character_dialogue"],
                "image_path": t["image_path"],
                "voice_path": t["voice_path"]
            })
        return turns, render_html(turns)
    except Exception as e:
        print(f"セッション読み込みエラー: {e}")
        return [], render_html([])

def update_session_list():
    return gr.update(choices=[s["dir"] for s in engine.list_sessions()])

# --------------------------------------------------
# チャット関数
# --------------------------------------------------
def chat(user_msg, turns, enable_image, enable_voice):
    if not user_msg.strip():
        yield "", turns, render_html(turns)
        return

    if not engine.current_run_dir:
        init_engine()

    turns = turns + [{"role": "user", "text": user_msg}]
    character_turn_added = False

    try:
        for result in engine.process_chat_turn_stream(
            user_msg,
            enable_image=enable_image,
            enable_voice=enable_voice,
        ):
            character_turn = {
                "role": "character",
                "text": result.get("character_dialogue", ""),
                "image_path": result.get("image_path"),
                "voice_path": result.get("voice_path"),
                "media_pending": result.get("status") == "generating_media",
            }
            if character_turn_added:
                turns[-1] = character_turn
            else:
                turns = turns + [character_turn]
                character_turn_added = True
            yield "", turns, render_html(turns)
    except Exception as e:
        error_text = str(e).replace("<", "&lt;").replace(">", "&gt;")
        if character_turn_added:
            turns[-1]["media_pending"] = False
            turns[-1]["media_error"] = error_text
            yield "", turns, render_html(turns)
            return
        error_turn = {
            "role": "character",
            "text": f"🚨 エラー: {error_text}",
            "image_path": None,
            "voice_path": None,
        }
        turns = turns + [error_turn]
        yield "", turns, render_html(turns)

# --------------------------------------------------
# カスタムCSS（モード切替対応版）
# --------------------------------------------------
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');

* { box-sizing: border-box; font-family: 'Noto Sans JP', system-ui, sans-serif; }

/* --- ライト/ダークモード共通のカスタム変数 --- */
:root {
    /* ライトモード時のデフォルト値 */
    --chat-bg: rgba(219,39,119,0.04);
    --chat-border: rgba(219,39,119,0.15);
    --chat-shadow: rgba(0,0,0,0.06);
    --header-bg: linear-gradient(135deg, rgba(124,58,237,0.06), rgba(219,39,119,0.06));
}

.dark {
    /* ダークモード時の値（Gradioが自動で.darkクラスを付与します） */
    --chat-bg: rgba(219,39,119,0.08);
    --chat-border: rgba(219,39,119,0.2);
    --chat-shadow: rgba(0,0,0,0.3);
    --header-bg: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(219,39,119,0.15));
}

/* ヘッダーエリア */
.app-header {
    background: var(--header-bg) !important;
    border: 1px solid var(--border-color-primary) !important;
    border-radius: 16px !important;
    padding: 16px 24px !important;
    margin-bottom: 12px !important;
    backdrop-filter: blur(10px) !important;
}

/* サイドパネル・アコーディオン（Gradioの変数を利用） */
.side-panel, .gr-accordion {
    background-color: var(--block-background-fill) !important;
    border: 1px solid var(--border-color-primary) !important;
    border-radius: 16px !important;
}

/* 送信ボタン（ここだけは常に目立たせる） */
button.primary {
    background: linear-gradient(135deg, #db2777, #f43f5e) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    box-shadow: 0 4px 15px rgba(219,39,119,0.3) !important;
    transition: all 0.2s ease !important;
}
button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(219,39,119,0.5) !important;
}

/* スクロールバー */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-color-primary); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #db2777; }

/* Gradio フッター非表示 */
footer { display: none !important; }
.gradio-container > .main > div > .wrap > .gap > footer { display: none !important; }
"""

# --------------------------------------------------
# Gradio UI 構築
# --------------------------------------------------
responsive_theme = gr.themes.Soft(
    primary_hue="pink",
    neutral_hue="slate",
).set(
    body_background_fill="#f9fafb",
    block_background_fill="#ffffff",
    input_background_fill="#f3f4f6",
    body_text_color="#1f2937",
    block_border_color="#e5e7eb",
    body_background_fill_dark="#0a0a14",
    block_background_fill_dark="rgba(255,255,255,0.03)",
    input_background_fill_dark="rgba(255,255,255,0.06)",
    body_text_color_dark="#e8e8f0",
    block_border_color_dark="rgba(255,255,255,0.08)",
)

with gr.Blocks(
    title="✨ AI Roleplay Chat",
    theme=responsive_theme,
    css=custom_css,
) as demo:

    turns_state = gr.State([])

    with gr.Row(elem_classes=["app-header"]):
        gr.HTML("""
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:28px;">✨</div>
            <div>
                <div style="font-size:22px; font-weight:700;
                    background:linear-gradient(135deg,#a78bfa,#f472b6);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    AI Roleplay Chat
                </div>
                <div style="font-size:12px; color:var(--body-text-color); opacity:0.6; margin-top:2px;">
                    Powered by AI Roleplay Engine
                </div>
            </div>
        </div>
        """)

    with gr.Column():
        chat_html = gr.HTML(render_html([]))

        with gr.Row():
            msg_box = gr.Textbox(
                placeholder="メッセージを入力... （Enterで送信）",
                show_label=False,
                scale=5,
                lines=1,
                max_lines=4,
            )
            send_btn = gr.Button("送信", variant="primary", scale=1, min_width=70)

        with gr.Accordion("⚙️ 設定", open=False, elem_classes=["side-panel"]):
            enable_img = gr.Checkbox(
                label="🖼️ 画像生成",
                value=engine.config.get("image", {}).get("enabled_by_default", True)
            )
            enable_voice = gr.Checkbox(
                label="🔊 音声読み上げ",
                value=engine.config.get("tts", {}).get("enabled_by_default", False)
            )
            gr.HTML("<div style='margin:12px 0; border-top:1px solid var(--border-color-primary);'></div>")
            clear_btn = gr.Button("🔄 新しいチャット", variant="secondary")

        with gr.Accordion("📂 過去のチャットを読み込む", open=False, elem_classes=["side-panel"]):
            session_dropdown = gr.Dropdown(
                choices=[s["dir"] for s in engine.list_sessions()], 
                label="セッション一覧"
            )
            refresh_sessions_btn = gr.Button("🔄 リスト更新", size="sm")
            load_session_btn = gr.Button("📂 このチャットを再開する", variant="primary")

    # --------------------------------------------------
    # イベントリスナー
    # --------------------------------------------------
    send_btn.click(
        chat,
        inputs=[msg_box, turns_state, enable_img, enable_voice],
        outputs=[msg_box, turns_state, chat_html],
    )
    msg_box.submit(
        chat,
        inputs=[msg_box, turns_state, enable_img, enable_voice],
        outputs=[msg_box, turns_state, chat_html],
    )
    clear_btn.click(
        init_engine,
        inputs=None,
        outputs=[turns_state, chat_html],
    )
    
    # 新規追加イベントリスナー
    load_session_btn.click(
        load_chat_history,
        inputs=[session_dropdown],
        outputs=[turns_state, chat_html]
    )
    refresh_sessions_btn.click(
        update_session_list,
        inputs=None,
        outputs=[session_dropdown]
    )

if __name__ == "__main__":
    init_engine()
    if engine.config.get("tts", {}).get("enabled_by_default", False):
        engine.preload_tts()
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=8501,
        share=False,
        inbrowser=False,
        allowed_paths=[str(Path(engine.base_dir).resolve())],
    )
