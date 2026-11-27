# Kindle Monitor - 本番デプロイ

**本番ファイル:** `kindle_display_enhanced.py`
**実行ラッパー:** `run_kindle_display.sh`（cron 用、pyenv / 環境変数を吸収）

## Cron 登録

自動セットアップ:

```bash
bash setup_cron.sh
```

手動:

```bash
crontab -e
```

```cron
*/15 * * * * cd /home/<user>/Projects/kindle_monitor/ && bash /home/<user>/Projects/kindle_monitor/run_kindle_display.sh >> /home/<user>/Projects/kindle_monitor/logs/run.log 2>&1
```

## テスト実行

```bash
cd /home/<user>/Projects/kindle_monitor
python3 kindle_display_enhanced.py
# または cron と同じ環境で
bash run_kindle_display.sh
```

## ログ確認

```bash
tail -f logs/kindle_monitor.log   # スクリプト本体のログ
tail -f logs/run.log              # cron の標準出力/エラー
```

## 表示内容

- 左ナビゲーション（32% 幅）: 時刻・日付・曜日、CPU% / CPU°C / GPU% / Mem%、天気予報
- メインパネル: Environment カード（Temp/Humi/Rain）、Storage カード（Home / `/dev/sda3`）、
  CPU% トレンド（24h）、CPU/GPU 温度トレンド（24h）、月間カレンダー（祝日対応）
- 解像度 768×1024（Paperwhite Gen.5）

詳細は `README.md` を参照してください。
