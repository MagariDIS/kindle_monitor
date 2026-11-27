# Kindle Monitor v3 - DESIGN実装完了

DESIGN.mdで設計した Kindle Paperwhite Gen10向けのレイアウトを実装しました。

## ✅ 実装内容（Phase 1 + 2）

### Phase 1: 基本構造
- ✅ 解像度: 1072×1448 px（Kindle Paperwhite Gen10対応）
- ✅ 2カラムレイアウト：左ナビ（22%）+ メインパネル（78%）
- ✅ 安全領域: 上から1303 px（下145 px は見切れ想定）

### Phase 2: グラフ機能
- ✅ 過去24時間データ記録（最大144データポイント）
- ✅ CPU使用率の面積グラフ描画
- ✅ 警告閾値ライン（75%）表示
- ✅ データ永続化（`~/.kindle_monitor_data.json`）

---

## 📐 レイアウト詳細

### 左ナビゲーション（X: 8–244, 高さ: 1303）

**Top（時刻表示）**
- 大きな時刻: `HH:MM`（90pt等幅フォント）
- 日付・曜日: `MM/DD (Day)`（18pt）

**Middle（センサーカード）**
- 4枚のカード：CPU%, CPU°C, GPU%, メモリ%
- 各カード：ラベル + 大きな数値（32pt）
- カード間マージン: 8px

**Bottom（将来拡張用）**
- アラート領域（未実装）

### メインパネル（X: 260–1064, 高さ: 1303）

**上段（Top Cards）**
- 左：System Summary（CPU, Temp, Memory）
- 右：Environment（気温, 湿度, 天気, 降水確率）
- 高さ: 280px
- 各カード: 背景色 #e0e0e0, 枠線

**中段（グラフ領域）**
- タイトル: "24h Trend (CPU %)"
- 面積グラフ: X軸 = 時間, Y軸 = CPU使用率（0–100%）
- 警告閾値: 75% を点線で表示
- 高さ: 400px

**下段（カレンダー + API）**
- 左: カレンダー（月表示, 今日をハイライト）
- 右: Claude API 使用率表示
- 高さ: 残り領域

---

## 📊 グラフ機能の詳細

### データ履歴管理

```python
# ~/.kindle_monitor_data.json
{
  "cpu_pct": [3, 1, 4, 8, 0, 5, ...],    # CPU使用率（直近144データ）
  "gpu_pct": [0, 0, 0, 0, 0, 0, ...],    # GPU使用率（直近144データ）
  "last_update": "2026-06-21T08:58:00"   # 最終更新時刻
}
```

### 描画処理

1. **起動時**: `~/.kindle_monitor_data.json` を読み込み
2. **実行時**: 最新のCPU/GPU使用率を記録
3. **グラフ描画**: deque内のデータを使用して面積グラフを描画
4. **保存**: 実行終了時に更新したデータを保存

---

## 🚀 使用方法

### 基本実行

```bash
cd /home/tmagari/Projects/kindle_monitor
python3 kindle_display_design_v3.py
```

### Cron登録（30分間隔）

```bash
# setup_cron.sh を修正して v3 を使用するように変更
cp /home/tmagari/Projects/kindle_monitor/.env.kindle.template ~/.env.kindle
nano ~/.env.kindle  # API キーを入力

# crontab に登録（v3版）
crontab -e
# 以下を追加:
# */30 * * * * source ~/.env.kindle 2>/dev/null && /home/tmagari/Projects/kindle_monitor/run_kindle_display.sh
```

ラッパースクリプト（`run_kindle_display.sh`）を以下のように編集：

```bash
PYTHON_SCRIPT="$SCRIPT_DIR/kindle_display_design_v3.py"  # v2 から v3 に変更
```

---

## 🎨 ビジュアル

### カラーパレット（電子ペーパー最適化）

| 用途 | 値 | 説明 |
|------|-----|------|
| 背景 | 255 | 白 |
| カード背景 | 220 | 淡灰 |
| 枠線 | 100 | 濃灰 |
| テキスト | 0 | 黒 |
| グラフ塗り | 200 | 中灰 |
| グラフ線 | 0 | 黒 |
| 閾値線 | 150 | 濃灰（破線） |

### フォント設定

| 用途 | フォント | サイズ |
|------|----------|--------|
| 時刻 | DejaVuSansMono-Bold | 90pt |
| 大数値 | Noto Sans CJK | 48pt |
| ラベル | Noto Sans CJK Regular | 14pt |
| 日付 | Noto Sans CJK Medium | 18pt |
| カレンダー | Noto Sans Mono | 14pt |

---

## 📈 グラフの特性

### データポイント

- **最大保持数**: 144データポイント
- **推奨更新間隔**: 10分（24時間 = 144 × 10分）
- **スケール**: 自動スケール（最大値を100%に正規化）

### グラフ表示

- **形式**: 面積グラフ（ポリゴン塗り + 線描画）
- **軸**: X軸 = 時間（均等分割）, Y軸 = 0–100%
- **目盛り**: なし（シンプル化）
- **警告ライン**: 75% に点線で表示

---

## 🔧 技術仕様

### ファイル構成

```
/home/tmagari/Projects/kindle_monitor/
├── kindle_display_design_v3.py    # メイン実装（最新版）
├── run_kindle_display.sh           # cron ラッパースクリプト（v3対応に修正）
├── .env.kindle.template            # 環境変数テンプレート
├── config.yaml                     # アプリケーション設定
├── ~/.kindle_monitor_data.json     # グラフデータ履歴（自動生成）
└── DESIGN_V3_COMPLETE.md          # このファイル
```

### 依存関係

```
PIL/Pillow      - 画像生成
requests        - HTTP通信
paramiko        - SSH/SFTP
psutil          - システムメトリクス
numpy/matplotlib - グラフ計算（未使用, PIL のみで実装）
yaml            - 設定ファイル解析
jpholiday       - 日本の祝日判定
```

---

## 🐛 既知の制限

| 項目 | 制限 | 対策 |
|------|------|------|
| **グラデーション** | PIL では限定的 | ポリゴン塗りで近似 |
| **ハッチパターン** | 実装なし | 単色で代替 |
| **スパークライン** | Phase 2 未対応 | Phase 3 で追加 |
| **複数グラフ** | CPU のみ | Phase 2.5 で GPU/メモリ追加 |
| **リアルタイム更新** | 静止画のみ | e-ink の特性上必要ない |

---

## 📝 次のステップ（Phase 3）

### 優先順位（推奨）

1. **Phase 2.5**: GPU / メモリ / ネットワークのグラフ追加
2. **Phase 3**: グラデーション＆細部デザイン調整
3. **Phase 4**: スパークライン＆アラート機能
4. **Phase 5**: WebUI ダッシュボード

### 試験運用

```bash
# v3版でcron運用開始
bash setup_cron_v3.sh  # 別途作成予定

# 監視
tail -f /var/log/kindle_monitor.log

# グラフデータ確認
cat ~/.kindle_monitor_data.json | python3 -m json.tool
```

---

## ✨ 改善内容（v2 → v3）

| 項目 | v2 | v3 | 改善内容 |
|------|----|----|--------|
| **解像度** | 758×1024 | 1072×1448 | Kindle 実解像度対応 |
| **レイアウト** | 縦積み | 2カラム | DESIGN.md に準拠 |
| **グラフ** | ❌ | ✅ | 24h トレンド表示 |
| **データ履歴** | ❌ | ✅ | JSON 永続化 |
| **カレンダー** | ✅ | ✅ | 祝日対応継続 |
| **セーフエリア** | ❌ | ✅ | 1303px までに重要情報 |

---

## 📞 トラブルシューティング

### Q: グラフが表示されない

**A:** データ履歴ファイルを確認

```bash
# ファイル確認
ls -la ~/.kindle_monitor_data.json

# 内容確認
python3 -c "import json; print(json.load(open('$HOME/.kindle_monitor_data.json')))['cpu_pct'])" | wc -w
# 出力が 144 未満の場合、複数回実行してデータを蓄積

# 強制リセット
rm ~/.kindle_monitor_data.json
```

### Q: テキストが重なっている

**A:** フォントサイズを調整（以下を参考）

- 時刻: 90pt → 70pt（小さくしたい場合）
- 数値: 48pt → 36pt
- ラベル: 14pt → 12pt

### Q: グラフが崩れている

**A:** データの最大値が 0 の場合

```python
# kindle_display_design_v3.py の draw_area_graph を修正
if max_val == 0:
    max_val = 1  # ゼロ除算対策
```

---

## 📄 ファイル

- `kindle_display_design_v3.py`: メイン実装
- `DESIGN.md`: 元の設計ドキュメント
- `DESIGN_V3_COMPLETE.md`: このファイル（実装完了報告）

---

**Status: ✅ Phase 1 + 2 実装完了 / Phase 3 以降は将来実装予定**

実装日: 2026-06-21
