# Cron 設定の更新（v3.1-final対応）

本番版を `kindle_display_final_production.py` に変更しました。

## 現在の Cron 設定確認

```bash
crontab -l
```

以下のような行が見つかるはずです：

```cron
*/30 * * * * source ~/.env.kindle 2>/dev/null && cd /home/tmagari/Projects/kindle_monitor && python3 kindle_display_design_v3_768.py >> /var/log/kindle_monitor.log 2>&1
```

## 更新手順

### Step 1: Cron 編集

```bash
crontab -e
```

### Step 2: スクリプト名変更

**変更前:**
```cron
python3 kindle_display_design_v3_768.py
```

**変更後:**
```cron
python3 kindle_display_final_production.py
```

### Step 3: 保存して確認

```bash
crontab -l | grep kindle
```

以下が表示されることを確認：
```
*/30 * * * * source ~/.env.kindle 2>/dev/null && cd /home/tmagari/Projects/kindle_monitor && python3 kindle_display_final_production.py >> /var/log/kindle_monitor.log 2>&1
```

---

## 改善内容の詳細

### 左ナビゲーション

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| 幅 | 169px (22%) | 246px (32%) |
| 時刻表示 | はみ出し気味 | ✅ 完全表示 |
| フォント | 72pt | 72pt（変わらず、余裕あり） |

### メインパネル上段

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| 左カード | System | Environment |
| 右カード | Environment | **API** (新) |
| API 表示 | 下段に移動 | 上段で目立つ |
| エラー表示 | ❌ | ✅ 対応 |

### API カードの表示内容

**正常時:**
```
API
5h: 65%
7d: 33%
OK
```

**エラー時（例）:**
```
API
API: Auth Error
(retry next time)
```

その他のエラー表示：
- `API: Rate Limited` → 429 エラー
- 非表示 → API キー未設定

### メインパネル下段

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| カレンダー | 60% 幅 | 100% 幅（フル） |
| 日付フォント | 10pt | **20pt** (2倍) |
| 曜日フォント | 10pt | **20pt** (2倍) |
| 今日表示 | 小さい枠 | **大きい枠** |

---

## テスト実行

設定後、すぐにテストしたい場合：

```bash
source ~/.env.kindle
cd /home/tmagari/Projects/kindle_monitor
python3 kindle_display_final_production.py
```

ログ確認：
```bash
tail -5 /var/log/kindle_monitor.log
```

---

## ロールバック（念のため）

問題が発生した場合は、旧版に戻すことができます：

```bash
crontab -e

# 以下に変更:
# python3 kindle_display_design_v3_768.py
```

---

## よくあるエラーと対処

### Q: `ModuleNotFoundError`

**原因:** ファイルが見つからない  
**対処:** ファイル存在確認

```bash
ls -la /home/tmagari/Projects/kindle_monitor/kindle_display_final_production.py
```

### Q: カレンダーが表示されない

**原因:** 画像生成エラー  
**対処:** ログ確認

```bash
tail -20 /var/log/kindle_monitor.log | grep -i error
```

### Q: API 情報が「--」のまま

**原因:** 環境変数未設定  
**対処:** API キー確認

```bash
cat ~/.env.kindle | grep ANTHROPIC
```

---

## 完成チェックリスト

実装確認用チェックリスト：

- [ ] Cron 設定を更新した
- [ ] スクリプト名が `kindle_display_final_production.py` に変更されている
- [ ] `crontab -l` で確認した
- [ ] テスト実行で正常に動作している
- [ ] Kindle 画面で以下が確認できる：
  - [ ] 時刻がはみ出していない
  - [ ] Environment カード（Temp/Humi/Weather）が表示
  - [ ] API カード（5h/7d/ステータス）が表示
  - [ ] カレンダーが大きく表示されている
  - [ ] グラフが表示されている

---

## 次回以降の実行

Cron は自動的に以下のタイミングで実行されます：

```
00:00, 00:30, 01:00, 01:30, ...
(30分間隔)
```

ログを監視：
```bash
tail -f /var/log/kindle_monitor.log
```

---

**Updated:** 2026-06-21  
**Status:** ✅ Ready for production
