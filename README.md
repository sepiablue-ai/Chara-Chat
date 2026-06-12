# 🎨 Chara-Chat - 汎用AIロールプレイエンジン

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)](https://gradio.app/)
[![ComfyUI](https://img.shields.io/badge/Image-ComfyUI-green.svg)](https://github.com/comfyanonymous/ComfyUI)

高度なLLMと画像生成AI（ComfyUI）、音声合成AI（Irodori-TTS）を融合させた、汎用的なインタラクティブ・ロールプレイ・チャットエンジンです。
設定ファイル（`config.json`）とプロンプトファイルを書き換えるだけで、様々なオリジナルAIキャラクターと会話を楽しむことができるように設計されています。
デフォルトのキャラクターとして、20歳の明るく元気な女子大生「さやか」が設定されています。

---

## 🌟 主な機能

- **🧠 インテリジェント・チャット**: 単なる会話だけでなく、状況に応じた「地の文」や服装・場所の変化を厳密に追跡。
- **⚙️ 一元管理されたキャラクター設定**: プロンプトと `config.json` に設定をまとめることで、キャラクターの性格や服装を容易に変更可能。
- **🖼️ リアルタイム画像生成**: 会話の情景に合わせて、内部で最適化された ComfyUI ワークフローを呼び出し、画像を生成。
- **🔊 TTS 音声合成**: キャラクターのセリフを毎ターン音声合成し、ブラウザ上で即座に再生。
- **⚡ マルチGPU / シングルGPU 両対応**: `.env` ファイルと `config.json` の設定により、マルチGPUでの高速並列処理、あるいはシングルGPUでの直列処理を選択可能。

---

## 🖥️ 動作環境（システム要件）

本システムは複数のAIモデル（LLM, 画像生成, 音声合成）をローカルで稼働させるため、一定スペック以上のPC環境が必要です。

- **OS**: Windows 10 / 11
- **メモリ (RAM)**: 32GB以上推奨
- **GPU (VRAM)**: 
  - **最低要件**: VRAM 12GB 〜 16GB のNVIDIA製GPU 1枚（※シングルGPU直列処理モード推奨）
  - **推奨要件**: VRAM 12GB + 8GB 等のマルチGPU環境（※並列生成で高速動作可能）

---

## 🚀 セットアップと起動

### 1. 初回準備（Python仮想環境）

```bash
# 仮想環境の作成と有効化
python -m venv venv
venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定 (`.env`)

自身の環境に合わせて、各バックエンドエンジンのパスやGPU割り当てを設定します。
`.env.example` をコピーして `.env` を作成してください。

```bash
copy .env.example .env
```
`.env` ファイルをテキストエディタで開き、`LM_STUDIO_PATH` や `COMFYUI_PATH` を自身の環境に合わせて書き換えます。シングルGPU環境の場合は、`COMFYUI_GPU_ID=0` と `TTS_GPU_ID=0` に設定してください。

### 3. 起動と終了

- **起動**: プロジェクトルートにある **`start.bat`** をダブルクリックして実行します。全てのバックエンドが起動し、ブラウザが利用可能になるまで待機します。
- **終了**: **`stop.bat`** を実行してサービスを安全に終了させ、VRAMを解放します。

---

## ⚙️ シングルGPU環境での設定に関する注意

シングルGPU（例：RTX 3060 12GB や RTX 4080 16GB 等のGPU1枚）で実行する場合、画像生成と音声合成を同時に実行するとVRAM不足（OOM）でクラッシュする可能性があります。
その場合、`config.json` の設定で直列生成モードに変更してください。

```json
  "image": {
    "enabled_by_default": true,
    "parallel_generation": false
  }
```
※ `parallel_generation` を `false` にすることで、LLM完了後に「画像生成」→「音声生成」が順番に行われるようになり、VRAMを節約できます。

---

## 📂 プロジェクト構造

```
Chara-Chat/
├── app.py                     # Gradio メインUI
├── chat_engine.py             # LLM/ComfyUI/TTS連携・状態管理
├── start.bat                  # 一括起動バッチ
├── stop.bat                   # サービス終了バッチ
├── .env.example               # 環境変数のテンプレート
├── config.json                # 設定ファイル（キャラ・バックエンド設定）
├── requirements.txt           # Pythonパッケージリスト
├── prompts/                   # プロンプト設定ディレクトリ（さやかの設定）
│   ├── character_setting.md   # キャラクター性格設定
│   ├── main_ai_director.md    # AIディレクター指示プロンプト
│   └── voice_examples.md      # セリフ口調の参考例
└── workflow_api.json          # ComfyUI ワークフロー定義
```
