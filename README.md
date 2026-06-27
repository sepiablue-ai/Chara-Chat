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

### 2. LLMバックエンド（Ollama）の準備
本システムはローカルLLMサービスとして [Ollama](https://ollama.com/) を使用します。
1. Ollamaをインストールして起動しておきます。
2. 使用するモデル（デフォルトでは `gemma4:12b-it-qat`）をあらかじめプルしておきます。
   ```bash
   ollama pull gemma4:12b-it-qat
   ```

### 3. 環境変数の設定 (`.env`)

`.env.example` をコピーして `.env` を作成します。

```bash
copy .env.example .env
```
`.env` ファイルをテキストエディタで開き、`OLLAMA_MODEL` や各種GPU割り当てを自身の環境に合わせて書き換えます。シングルGPU環境の場合は、`COMFYUI_GPU_ID=0` と `TTS_GPU_ID=0` に設定してください。

### 4. 起動と終了

- **起動**: プロジェクトルートにある **`start.bat`** をダブルクリックして実行します。自動的にOllamaの動作確認、および各種サービス（ComfyUI, Irodori-TTS, Gradio）がバックグラウンドで起動します。
- **終了**: **`stop.bat`** を実行してサービスを終了させ、VRAMを解放します（Ollamaは起動したままになります）。

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
├── workflow_api.json          # ComfyUI ワークフロー定義
│
├── eval_state_cases.py        # 個別テストケース評価スクリプト
├── run_testcase_suite.py      # テストスイート一括実行スクリプト
├── summarize_testcase_results.py # テスト結果の要約表示スクリプト
└── testcase/                  # テストケース定義（Markdown）格納用ディレクトリ
```

---

## 🧪 MioTTSの実験的サポート（ストリーミング再生）

`feature/miotts-streaming` ブランチにて、音声合成エンジンとして [MioTTS](https://github.com/Aratako/MioTTS) によるリアルタイムの音声ストリーミング再生を実験的にサポートしています。

### ⚠️ 既知の課題
- **ストリーミング再生時のノイズ**:
  MioTTS からのストリーミング応答を順次受信しながら `PyAudio` でリアルタイム再生を行うと、現在音声がノイズまみれ（もしくは極端な細切れ）になる現象が発生しています。
- **一時的な回避策**:
  ストリーミングでのリアルタイム再生を使用せず、MioTTS 側の音声生成が完全に終了した後に、ブラウザ（Gradio UI）側の再生ボタン等から再生した場合は、ノイズのない非常にクリアな音声として再生されることが確認されています。

---

## 🧪 テストスイートの実行

本エンジンには、プロンプト変更によるキャラクターのセリフ、情景（シーン）、服装の判定挙動の変化を検証するための自動テスト環境が備わっています。

### 1. テストスイートの一括実行
[testcase/](file:///C:/Users/sepia/python/Chara-Chat/testcase/) ディレクトリ内の全てのテストケース（Markdown）を読み込み、自動的にロールプレイセッションを実行して判定精度を測定します。

```bash
# 仮想環境が有効な状態で実行
python run_testcase_suite.py [テストケースフォルダ] [制限件数] [--no-image]

# 例：testcaseフォルダのケースを画像生成なしで最大2件実行
python run_testcase_suite.py testcase 2 --no-image
```
実行結果は [testcase_results/](file:///C:/Users/sepia/python/Chara-Chat/testcase_results/) にJSONファイル（および設定されていれば画像ファイルのコンタクトシート）として出力されます。このディレクトリはGit管理外です。

### 2. 個別ケースの簡易実行
特定の短い対話ケースを指定して実行し、状態変化の履歴をターミナル上にJSON形式で出力します。

```bash
# ケースIDと画像生成の実行ターンを指定して実行
python eval_state_cases.py [ケースID(1〜5)] [画像生成を行うターン数(省略時は0)]

# 例：ケース1を実行し、3ターン目で画像を生成する
python eval_state_cases.py 1 3
```

### 3. テスト結果の要約表示
直近に実行したテストスイートの結果（`testcase_results/` 内の各JSONファイル）をパースし、各ターンの「想定（expected）」と「実際（actual）」の出力を一覧で比較します。

```bash
python summarize_testcase_results.py
```
