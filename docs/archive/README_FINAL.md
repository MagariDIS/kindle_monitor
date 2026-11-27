# Kindle Monitor - 最終実装版

**対応デバイス:** Paperwhite Gen.5（768×1024, 213ppi）

---

## 📦 バージョン比較

| 機能 | v2 | v3.1 |
|------|-----|------|
| **解像度** | 758×1024 | 768×1024 ✅ |
| **推奨度** | △ | ✅ **本番推奨** |
| **レイアウト** | シンプル | 2カラム |
| **グラフ機能** | ❌ | ✅ 24h トレンド |
| **データ永続化** | ❌ | ✅ JSON |
| **最適化** | 汎用 | Paperwhite Gen.5 専用 |

---

## 🎯 推奨実装

**本番環境では v3.1 を使用してください。**

```bash
cd /home/tmagari/Projects/kindle_monitor

# ファイル名
# kindle_display_design_v3_768.py  ← 本番版
```

---

## 🚀 セットアップ手順（v3.1用）

### Step 1: 環境変数設定

```bash
cp ~/.../kindle_monitor/.env.kindle.template ~/.env.kindle
nano ~/.env.kindle
chmod 600 ~/.env.kindle
```

### Step 2: Cron 登録（修正版）

```bash
# setup_cron.sh を一時的に修正
# または直接 crontab に追加:

crontab -e
# 以下を追加:
# */30 * * * * source ~/.env.kindle 2>/dev/null && cd /home/tmagari/Projects/kindle_monitor && python3 kindle_display_design_v3_768.py >> /var/log/kindle_monitor.log 2>&1
```

### Step 3: ログ監視

```bash
tail -f /var/log/kindle_monitor.log
```

---

## 📊 レイアウト仕様（768×1024）

```
┌─────────────────────────────────────────────────────┐
│  Left Nav (169px)  │  Main Panel (599px)           │
│  ┌───────────┐     │  ┌────────────┬────────────┐  │
│  │   09:20   │     │  │  System    │Environ     │  │
│  │ 06/21(Sun)│     │  │ CPU: 5     │Temp: 30°C  │  │
│  ├───────────┤     │  │ Temp: 45   │Humi: 30%   │  │
│  │CPU%: 5    │     │  │ Mem: 22    │Weather: 雨 │  │
│  ├───────────┤     │  └────────────┴────────────┘  │
│  │CPU°C: 45  │     │  ┌────────────────────────┐  │
│  ├───────────┤     │  │ 24h Trend (CPU %)      │  │
│  │GPU%: 0    │     │  │        /\              │  │
│  ├───────────┤     │  │      /  \____    ____/\│  │
│  │Mem%: 22   │     │  │     /        \__/      │  │
│  └───────────┘     │  └────────────────────────┘  │
│                    │  ┌──────────────┬────────┐   │
│                    │  │ 2026-06      │ API    │   │
│                    │  │ 1  2  3  ... │ --     │   │
│                    │  └──────────────┴────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 データ永続化

グラフ機能は JSON ファイルでデータを保存：

```bash
# データファイルの場所
~/.kindle_monitor_data.json

# 中身確認
python3 -c "import json; d=json.load(open('$HOME/.kindle_monitor_data.json')); print(f\"CPU data: {len(d['cpu_pct'])} points\")"

# リセット（必要な場合）
rm ~/.kindle_monitor_data.json
```

**24時間分のデータ（144ポイント）が蓄積されると、完全な1日分グラフが表示されます。**

---

## 📈 グラフの特性

### 更新間隔

- **推奨:** 30分ごと（Cron で自動実行）
- **最大保持:** 144ポイント（24時間 × 10分想定）
- **スケール:** 自動調整（0–100%）

### 表示内容

- **データ:** CPU使用率（リアルタイム）
- **警告ライン:** 75%（点線）
- **フォーマット:** 面積グラフ + 線

---

## 🎨 最適化済みフォント

Paperwhite Gen.5 (213ppi) 向けに調整：

| 用途 | フォント | サイズ |
|------|----------|--------|
| 時刻 | DejaVuSansMono-Bold | 72pt |
| 大数値 | Noto Sans CJK Bold | 40pt |
| ラベル | DejaVuSansMono | 12pt |
| 日付 | Noto Sans CJK Medium | 16pt |

---

## 🔍 トラブルシューティング

### Q: テキストが小さい/大きい

**A:** フォントサイズを調整（`kindle_display_design_v3_768.py`内）

```python
# 時刻を大きくしたい場合
font_time = ImageFont.truetype(..., 80)  # 72 から変更

# ラベルを大きくしたい場合
font_label_en = ImageFont.truetype(..., 14)  # 12 から変更
```

### Q: グラフが表示されない

**A:** データが蓄積されるまで待機

```bash
# 複数回実行してデータを蓄積
for i in {1..5}; do python3 kindle_display_design_v3_768.py; sleep 2; done

# データポイント確認
python3 -c "import json; print(json.load(open('$HOME/.kindle_monitor_data.json'))['cpu_pct'])"
```

### Q: Kindle に表示されない

**A:** SSH 接続を確認

```bash
# 接続テスト
ssh root@10.0.1.143 "echo OK"

# パスワード確認
cat config.yaml | grep password
```

---

## 📝 ファイル一覧

```
/home/tmagari/Projects/kindle_monitor/
├── kindle_display_design_v3_768.py  ← 本番版（推奨）
├── kindle_display_pro_v2.py         ← 旧版（v2）
├── run_kindle_display.sh            ← Cron ラッパー
├── setup_cron.sh                    ← セットアップ
├── .env.kindle.template             ← 環境変数テンプレート
├── config.yaml                      ← 設定ファイル
├── START_HERE.md                    ← クイックガイド
├── DESIGN.md                        ← 設計（1072×1448）
├── DESIGN_V3_COMPLETE.md            ← v3 実装レポート
└── README_FINAL.md                  ← このファイル
```

---

## 🎯 実装スタータス

| 機能 | 状態 | 備考 |
|------|------|------|
| **センサーデータ取得** | ✅ | Wio Link, 天気API |
| **システムモニタリング** | ✅ | CPU, GPU, メモリ温度 |
| **Claude API 使用率** | ✅ | 5時間・7日単位表示 |
| **カレンダー** | ✅ | 祝日対応済 |
| **Kindle 転送** | ✅ | SSH/SFTP |
| **Cron 自動実行** | ✅ | 30分間隔 |
| **24h グラフ** | ✅ | CPU使用率トレンド |
| **データ永続化** | ✅ | JSON形式 |

---

## 💡 今後の拡張（参考）

### Phase 2.5: 複数グラフ
- GPU/メモリ/ネットワークのグラフ追加

### Phase 3: デザイン調整
- グラデーション対応
- ハッチパターン実装
- スパークライン追加

### Phase 4: アラート機能
- 異常値の自動検知
- 通知機能追加

---

## 📞 サポート

### 問い合わせ情報

- **設定:** `config.yaml` を確認
- **ログ:** `/var/log/kindle_monitor.log`
- **データ:** `~/.kindle_monitor_data.json`

### よくあるエラー

| エラー | 原因 | 解決方法 |
|--------|------|--------|
| `Config file not found` | config.yaml がない | ファイル確認 |
| `ANTHROPIC_API_KEY` 未設定 | 環境変数がない | `~/.env.kindle` 確認 |
| `Connection refused` | Kindle が起動していない | Kindle 再起動 |
| グラフが表示されない | データが足りない | 複数回実行 |

---

## ✨ バージョン履歴

- **v2** (2026-06-21): Pro版リリース（758×1024）
- **v3** (2026-06-21): DESIGN.md実装（1072×1448）
- **v3.1** (2026-06-21): Paperwhite Gen.5 最適化（768×1024） ← **本番版**

---

## 🎉 完成！

**実装完了日:** 2026-06-21

すべての機能が統合されました。本番環境でのご利用をお願いします。

Questions? See SETUP_CRON_QUICK.md or CRON_SETUP.md for detailed guides.
