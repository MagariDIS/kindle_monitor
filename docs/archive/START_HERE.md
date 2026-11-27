# Kindle Monitor - スタートアップガイド

Kindle e-ink ディスプレイに環境センサーデータを自動表示するシステムの設定ガイドです。

## 🚀 セットアップ（3ステップ）

### Step 1: API キー設定

```bash
# テンプレートをコピー
cp ~/.../kindle_monitor/.env.kindle.template ~/.env.kindle

# API キーを編集
nano ~/.env.kindle
# sk-ant-... の部分を実際のキーに置き換える

# 権限設定（重要！秘密鍵保護）
chmod 600 ~/.env.kindle
```

### Step 2: Cron ジョブ登録（自動化）

```bash
cd /home/tmagari/Projects/kindle_monitor
bash setup_cron.sh
```

このコマンドが自動的に以下を実行します：
- ✅ ラッパースクリプト設定
- ✅ ログディレクトリ作成
- ✅ Crontab 登録（30分間隔）
- ✅ テスト実行

### Step 3: ログ監視

```bash
# リアルタイムでログを監視
tail -f /var/log/kindle_monitor.log
```

成功時の出力例：
```
2026-06-21 00:45:00 - INFO - Starting Kindle display update (pro v2)
2026-06-21 00:45:05 - INFO - Wio Link: temp=29.0C, humidity=29%
2026-06-21 00:45:06 - INFO - Image saved: /tmp/panel.png
2026-06-21 00:45:06 - INFO - Complete
```

---

## 📊 実行スケジュール

| 時刻 | 実行 |
|------|------|
| 00:00 | ✓ |
| 00:30 | ✓ |
| 01:00 | ✓ |
| 01:30 | ✓ |
| ... | (30分ごと) |

---

## ✅ チェックリスト

- [ ] API キーを ~/.env.kindle に設定
- [ ] chmod 600 ~/.env.kindle で権限設定
- [ ] bash setup_cron.sh でセットアップ実行
- [ ] tail -f /var/log/kindle_monitor.log で動作確認
- [ ] Kindle ディスプレイが更新されることを確認

---

## 📚 ドキュメント

| ファイル | 内容 |
|----------|------|
| **SETUP_CRON_QUICK.md** | Cron セットアップ（クイック版） |
| **CRON_SETUP.md** | Cron セットアップ（詳細版） |
| **CLAUDE.md** | プロジェクト全体の説明 |
| **config.yaml** | アプリケーション設定 |

---

## 🔧 トラブルシューティング

### Q: "ANTHROPIC_API_KEY not set" エラー

**A:** API キーを ~/.env.kindle に設定してください

```bash
nano ~/.env.kindle
# sk-ant-... に置き換える
source ~/.env.kindle
echo $ANTHROPIC_API_KEY  # 確認
```

### Q: Cron ジョブが実行されない

**A:** ジョブが登録されているか確認

```bash
crontab -l | grep kindle
```

登録されていない場合は setup_cron.sh を再実行してください。

### Q: ログファイルに権限がない

**A:** ログディレクトリの権限を確認

```bash
# /var/log に書き込めない場合
mkdir -p ~/logs
export LOG_FILE="$HOME/logs/kindle_monitor.log"
```

その後、setup_cron.sh で設定を更新してください。

---

## 🛑 ジョブ管理

### 一時停止

```bash
crontab -e
# 該当行の先頭に # を付ける
```

### 再開

```bash
crontab -e
# # を削除
```

### 削除

```bash
crontab -r
```

---

## 🔒 セキュリティ

✅ **実装済み**
- API キーは環境変数で管理（コードに埋め込まない）
- ~/.env.kindle のパーミッション: 600（本人のみ読み取り）
- ログには秘密鍵は記録されない

---

## 次のステップ

- 📊 月1回、API 使用率をチェック
- 📈 必要に応じてスケジュール調整（15分 or 1時間）
- 🔄 ログファイルの定期的なローテーション

---

**準備完了！🎉 自動実行開始です。**

詳細は SETUP_CRON_QUICK.md または CRON_SETUP.md をご覧ください。
