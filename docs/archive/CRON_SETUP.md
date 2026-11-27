# Kindle Monitor - Cron Setup Guide

Kindle display を30分間隔で自動更新するジョブを設定します。

## 1. 環境変数の設定

### Option A: 環境変数ファイル（推奨）

```bash
# ~/.env.kindle ファイルを作成
cat > ~/.env.kindle << 'EOF'
export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"
EOF

# 権限を制限（秘密鍵を含むため）
chmod 600 ~/.env.kindle
```

### Option B: .bashrc に追加

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## 2. ログディレクトリの準備

```bash
# ログディレクトリ作成（sudo 必要な場合）
sudo mkdir -p /var/log
sudo touch /var/log/kindle_monitor.log
sudo chown $USER:$USER /var/log/kindle_monitor.log

# または、ホームディレクトリ配下を使用
mkdir -p ~/logs
export LOG_FILE="$HOME/logs/kindle_monitor.log"
```

## 3. Cron ジョブを追加

```bash
# crontab 編集を開始
crontab -e

# 以下の行を追加（30分間隔で実行）
*/30 * * * * export ANTHROPIC_API_KEY="sk-ant-your-key-here" && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh

# または ~/.env.kindle を使用する場合：
*/30 * * * * source ~/.env.kindle && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh
```

## 4. 実行確認

```bash
# crontab の設定を確認
crontab -l

# ログ出力をリアルタイムで監視
tail -f /var/log/kindle_monitor.log

# または（ホームディレクトリ配下の場合）
tail -f ~/logs/kindle_monitor.log
```

## 5. スケジュール例

| 間隔 | Cron 表記 | 用途 |
|------|----------|------|
| **30分** | `*/30 * * * *` | 推奨（バランス型） |
| **15分** | `*/15 * * * *` | より頻繁に更新 |
| **1時間** | `0 * * * *` | 少なめの更新 |
| **4時間** | `0 */4 * * *` | API制限が厳しい場合 |

## 6. トラブルシューティング

### ジョブが実行されない
```bash
# cron サービス状態確認
sudo systemctl status cron

# cron ログを確認（システムによって異なる）
sudo journalctl -u cron
# または
sudo grep CRON /var/log/syslog | tail -20
```

### 権限エラー
```bash
# スクリプトが実行可能か確認
ls -la /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh

# ログファイルに書き込み権限があるか確認
touch /var/log/kindle_monitor.log && echo "OK"
```

### API キー エラー
```bash
# 環境変数が正しく読み込まれているか確認
crontab -e

# 次のコマンドでテスト
bash -c 'source ~/.env.kindle && echo $ANTHROPIC_API_KEY'
```

## 7. Cron ジョブ実行ログの確認

```bash
# 最新10行を表示
tail -10 /var/log/kindle_monitor.log

# リアルタイム監視
tail -f /var/log/kindle_monitor.log

# エラーのみ抽出
grep ERROR /var/log/kindle_monitor.log

# 特定の日時のログ
grep "2026-06-21" /var/log/kindle_monitor.log
```

## 8. Cron ジョブの停止・削除

```bash
# 特定のジョブをコメントアウト（crontab -e で編集）
# */30 * * * * source ~/.env.kindle && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh

# 全ジョブを削除
crontab -r

# 確認
crontab -l
```

## 9. セキュリティのベストプラクティス

✅ **推奨**
- API キーは `~/.env.kindle` に保存（権限 600）
- ログファイルに秘密鍵は記録しない
- SSH キー認証を Kindle に設定

❌ **避けるべき**
- crontab に直接 API キーを記載
- API キーを環境変数で公開
- ログファイルを世界読み取り可能に設定

## 10. 実行例

```bash
# 設定完了後、次の30分刻みで自動実行開始
# 例: 設定時刻が 14:25 なら、14:30, 15:00, 15:30, ... に実行

# 手動でテスト実行
source ~/.env.kindle && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh

# ログ確認
tail -20 /var/log/kindle_monitor.log
```
