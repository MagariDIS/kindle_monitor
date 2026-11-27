# Kindle Monitor - Cron Setup (クイックガイド)

30分間隔でKindleディスプレイを自動更新するジョブを設定します。

## セットアップ方法（推奨）

### 方法1: 自動セットアップスクリプト（推奨）

```bash
cd ~/Projects/kindle_monitor
bash setup_cron.sh
```

このスクリプトが自動的に以下を実行します：
- ✅ 環境変数ファイル作成（`~/.env.kindle`）
- ✅ ラッパースクリプト設定
- ✅ ログディレクトリ作成
- ✅ Crontab に登録
- ✅ テスト実行

---

### 方法2: 手動セットアップ

**Step 1: 環境変数ファイルを作成**

```bash
cp /home/tmagari/Projects/kindle_monitor/.env.kindle.template ~/.env.kindle
chmod 600 ~/.env.kindle
nano ~/.env.kindle
```

`sk-ant-...` の部分を実際の API キーに置き換えて保存します。

**Step 2: Crontab に登録**

```bash
crontab -e
```

以下の行を追加：

```cron
# Kindle Monitor - Display update every 30 minutes
*/30 * * * * source ~/.env.kindle 2>/dev/null && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh
```

**Step 3: 動作確認**

```bash
# ジョブが登録されたか確認
crontab -l

# ログを監視（リアルタイム）
tail -f /var/log/kindle_monitor.log
# または（ホームディレクトリ配下の場合）
tail -f ~/logs/kindle_monitor.log
```

---

## 実行スケジュール

| 時刻 | 実行状況 |
|------|--------|
| **00:00** | ✓ 実行 |
| **00:30** | ✓ 実行 |
| **01:00** | ✓ 実行 |
| **01:30** | ✓ 実行 |
| ... | (繰り返し) |

---

## トラブルシューティング

### Q: ジョブが実行されない

```bash
# cron サービス確認
sudo systemctl status cron

# cron ログ確認
sudo journalctl -u cron | tail -20

# または（古い OS）
sudo tail -50 /var/log/syslog | grep CRON
```

### Q: API エラーが出ている

```bash
# 環境変数が読み込まれているか確認
source ~/.env.kindle && echo "API Key: ${ANTHROPIC_API_KEY:0:20}..."

# API キーの形式確認（sk-ant- で始まるか）
grep ANTHROPIC ~/.env.kindle
```

### Q: ログファイルに権限がない

```bash
# ログファイル作成（sudo 不要の場合）
mkdir -p ~/logs
touch ~/logs/kindle_monitor.log

# setup_cron.sh の LOG_FILE 変数を変更
export LOG_FILE="$HOME/logs/kindle_monitor.log"
```

---

## ジョブの管理

### ジョブを確認

```bash
crontab -l
```

### ジョブを編集

```bash
crontab -e
# その行を編集または削除
```

### ジョブを一時停止

```bash
crontab -e
# 行の先頭に # を付ける
# */30 * * * * source ~/.env.kindle 2>/dev/null && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh
```

### すべてのジョブを削除

```bash
crontab -r
```

---

## ログ監視

### リアルタイムで監視

```bash
tail -f /var/log/kindle_monitor.log
```

### 最新10行を表示

```bash
tail -10 /var/log/kindle_monitor.log
```

### エラーを検索

```bash
grep -i error /var/log/kindle_monitor.log
```

### 特定の日付のログを表示

```bash
grep "2026-06-21" /var/log/kindle_monitor.log
```

---

## セキュリティ設定

### ✅ 推奨設定

```bash
# 環境変数ファイルのパーミッション（本人のみ読み取り可能）
chmod 600 ~/.env.kindle

# 確認
ls -la ~/.env.kindle
# -rw------- と表示されればOK
```

### ❌ 避けるべき設定

- crontab に直接 API キーを記載
- `chmod 644` で環境変数ファイルをパブリック化
- API キーをシェル履歴に残す

---

## 実行例

```bash
# セットアップ実行
$ bash setup_cron.sh

========================================
Kindle Monitor - Cron Job Setup
==========================================

Step 1: Creating environment file
--------
✓ Created: /home/tmagari/.env.kindle (permissions: 600)

IMPORTANT: Edit /home/tmagari/.env.kindle and replace the placeholder with your actual API key:
  nano /home/tmagari/.env.kindle

Press Enter after you've set the API key...
[ユーザーがここでエディタを開く]

Step 2: Verifying wrapper script
--------
✓ Wrapper script is executable: /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh

Step 3: Setting up log directory
--------
✓ Log file: /var/log/kindle_monitor.log

Step 4: Adding to crontab
--------
✓ Added cron job: every 30 minutes

Entry:
*/30 * * * * source ~/.env.kindle 2>/dev/null && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh

Step 5: Test run
--------
Running once to verify configuration...

2026-06-21 00:45:00,123 - INFO - Starting Kindle display update (pro v2)
2026-06-21 00:45:05,234 - INFO - Wio Link: temp=29.0C, humidity=29%
2026-06-21 00:45:05,500 - INFO - Image saved: /tmp/panel.png
2026-06-21 00:45:06,000 - INFO - Connected to Kindle
2026-06-21 00:45:06,100 - INFO - Complete

==========================================
Setup Complete!
==========================================

✓ Environment file: /home/tmagari/.env.kindle
✓ Wrapper script: /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh
✓ Log location: /var/log/kindle_monitor.log
✓ Cron interval: every 30 minutes (*/30 * * * *)

Next runs:
  2026-06-21 01:00
  2026-06-21 01:30

Monitor logs:
  tail -f /var/log/kindle_monitor.log
```

---

## 次のステップ

- ✅ cron で自動実行開始
- ✅ ログファイルをモニタリング
- 📊 月1回、API 使用率を確認
- 🔄 必要に応じてスケジュール調整

---

## サポート情報

詳細は以下を参照：
- `CRON_SETUP.md` - 詳細なセットアップガイド
- `CLAUDE.md` - プロジェクト全体の説明
- `config.yaml` - 設定ファイル
