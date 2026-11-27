# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kindle Paperwhite Gen.5 (768×1024, 213ppi) の e-ink ディスプレイに、センサー・システム情報・天気・ストレージ・カレンダーを描画するダッシュボード。

- 本番スクリプト: `kindle_display_enhanced.py`（唯一の本番版）
- cron ラッパー: `run_kindle_display.sh`（pyenv 絶対パス python を使用、`~/.env.kindle` を読み込み）
- `kindle_display_*.py`（enhanced 以外）、`kindle_calendar.py` は過去バージョン。**変更・参照の対象にしない**

## Architecture

```
get_wio_link_data / get_weather_data / get_cpu_* / get_gpu_* /
get_memory_usage / get_storage_usage
        ↓
DATA_HISTORY (deque 144点 = 24h, ~/.kindle_monitor_data.json に永続化)
        ↓
create_image()  … PIL で 768×1024 グレースケール描画
        ↓
upload_to_kindle()  … /tmp/panel.png → SFTP(paramiko) → eips で表示
```

### レイアウト（`create_image()`）
- 左ナビ（幅 32%）: 時刻(72pt)・日付・曜日、CPU%/CPU°C/GPU%/Mem%、今日/明日の天気と説明文
- メイン: Environment カード（Temp/Humi/Rain）、Storage カード（Home FS と `/dev/sda3` のドーナツ）、
  CPU% トレンド、CPU/GPU 温度トレンド（各 24h）、月間カレンダー（jpholiday で祝日）
- グレースケール: 0=数値/本文, 80–120=ラベル/補助線, 210–245=背景/カード
- セーフエリアは高さの 90%

### 主な関数
- `load_config()` … `config.yaml` を読み込み（無ければ終了）
- `get_claude_usage()` / `get_claude_oauth_token()` … 実装済みだが **現状 `create_image()` から呼ばれていない**（画面に出ない）
- `draw_donut` / `draw_grid_25` / `draw_area_graph` / `wrap_japanese_text` … 描画ヘルパー

## Dependencies

`pip install -r requirements.txt`（PyYAML, Pillow, requests, numpy, paramiko, jpholiday, pytz, iso8601, psutil）。
GPU は `nvidia-smi`、ストレージ検出は `findmnt` を使用。

## Configuration

- `config.yaml`（git 管理外。テンプレートは `config.yaml.example`）
  - `kindle.ip_address` / `kindle.ssh.{username,password,private_key_path,port,timeout}` / `sftp_target` / `display_command`
  - `sensors.wio_link.{base_url,sensor.{node_id,access_token,temp_key,humi_key}}`
  - `sensors.weather.city_code`（tsukumijima.net, 270000=大阪）
  - `fonts`（Noto Sans CJK + DejaVu）、`anthropic`（任意）
- `~/.env.kindle`（任意、`.env.kindle.template` 参照）: `ANTHROPIC_API_KEY`（フォールバック）、`LOG_FILE`
- 注意: `upload_to_kindle()` は現状 `ssh.password` のみ使用（`private_key_path` は未対応）。`kindle.ip_address` へ直接接続（netdiscover は使わない）

## Running

```bash
python3 kindle_display_enhanced.py      # 手動実行
bash run_kindle_display.sh              # cron と同じ環境で実行
bash setup_cron.sh                      # cron 登録（15分間隔）
```

cron（15分間隔）:
```cron
*/15 * * * * cd /path/to/kindle_monitor/ && bash /path/to/kindle_monitor/run_kindle_display.sh >> /path/to/kindle_monitor/logs/run.log 2>&1
```

ログ: `logs/kindle_monitor.log`（ラッパー経由）、`logs/run.log`（cron 出力）。

## セキュリティ

- `config.yaml` / `.env.kindle` / 鍵ファイルは `.gitignore` 済み。**秘密情報をコード・ドキュメント・コミットに含めない**
- Kindle の SSH は鍵認証が推奨:
  ```bash
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/kindle_id_rsa -N ""
  ssh-copy-id -i ~/.ssh/kindle_id_rsa.pub root@<kindle-ip>
  ```
  `config.yaml` の `kindle.ssh.private_key_path` に指定（※ 上記のとおりコード側の対応が必要）
- `~/.env.kindle` は `chmod 600`

## Known Issues

1. フォント・アイコン・API エンドポイントは環境依存（Noto CJK が必要）
2. Claude 使用率は取得のみで未描画
3. `upload_to_kindle()` は鍵認証未対応、`AutoAddPolicy` でホスト鍵を無検証受け入れ
4. ストレージ対象 `/dev/sda3` は `get_storage_usage()` にハードコード
5. 過去バージョン時点のドキュメント（`CRON_SETUP.md`, `START_HERE.md`, `README_FINAL.md`, `DESIGN*.md` など）は `docs/archive/` に退避済みで、現行実装とは一致しない（正は `README.md` / `DEPLOYMENT.md`）
