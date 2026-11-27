### 概要
Kindle Paperwhite Gen10（**6インチ / 300ppi / 解像度 1072×1448 px 想定**）向けに、**左ナビ＋メインパネル（B案）**をベースに、A案の大グラフを組み込んだ**1ページ完結ワイヤーフレーム**を作成します。  
**注意**：下側10%（高さ）が見切れる前提なので、**安全領域は上から90%**（重要情報はここに収める）に限定します。

---

### キャンバスとセーフエリア（前提値）
- **デバイス解像度（想定）**：**1072 px（幅） × 1448 px（高さ）**  
- **見切れを考慮したセーフエリア高さ**：\(1448 \times 0.90 = 1303\) **px**（下側145pxが見切れる）  
- **レイアウト比**：左ナビ **22%**（固定） / メイン **78%**

---

### 画面グリッド（ピクセル指定）
| 項目 | 値 |
|---|---:|
| **全体キャンバス** | **1072 × 1448 px** |
| **セーフエリア** | **1072 × 1303 px**（Y=0..1302） |
| **左ナビ幅** | **236 px**（1072 × 0.22 → 235.84 → **236**） |
| **メイン幅** | **836 px**（残り） |
| **メイン上下分割** | 上段 30% → **391 px**; 中段 45% → **586 px**; 下段 25% → **326 px** |
| **左ナビ縦分割** | Top 28% → **365 px**; Middle 52% → **678 px**; Bottom 20% → **260 px** |

---

### 左ナビ（X:0–235, 高さ:1303）
- **Top（0–365 px）**  
  - **大時刻（HH:MM）**：中央寄せ、**フォントサイズ 140 px**（等幅推奨）、太字。  
  - **日付・曜日**：時刻下に小さく、**28 px**。
- **Middle（365–1042 px）** — 主要センサ縦スタック（各カード高さは可変）  
  - **CPU 使用率カード**：数値（**48 px 等幅**）＋小さなスパークライン（高さ 28 px）。  
  - **CPU 温度カード**：数値（**48 px**）＋状態アイコン（ハッチで警告表現）。  
  - **GPU / メモリ / ネットワーク**：同様のカードを縦に並べ、カード間マージン **12–16 px**。  
- **Bottom（1042–1302 px）** — アラート領域（1行）  
  - **簡易アラート**：アイコン＋1行テキスト（**20–24 px**）。重要なアラートは二重枠＋ハッチで強調。

---

### メインパネル（X:236–1071, 高さ:1303）
#### 上段カード行（高さ 391 px）
- **左：システムサマリ（幅 50% → 418 px）**  
  - 大きな数値群（CPU% / Temp / Mem%）を横並び。主要数値は**48–64 px 等幅**。  
  - 各数値下に短いラベル（**16–18 px**）。
- **右：環境カード（幅 50% → 418 px）**  
  - 室温（**48 px**）・湿度（**36 px**）・天気テキスト（**18–20 px**）・雨確率（小アイコン＋数値）。

#### 中段グラフ（高さ 586 px） ← **A案の大グラフ**
- **メイン面積チャート領域**（中央、左右マージン 16 px）  
  - **表示範囲**：過去24時間（横軸）／縦軸は選択指標（CPU% など）。  
  - **線幅**：2–3 px（電子ペーパーで潰れない太さ）。塗りは単色薄灰（階調1段）。  
  - **閾値ライン**：点線（中灰）＋右端に閾値ラベル（**14–16 px**）。  
- **下部にスパークライン群**（高さ合計 60–80 px）  
  - CPU / GPU / ネットワーク 各スパークライン（高さ 18–24 px、横並び）。

#### 下段（高さ 326 px） — カレンダー＋イベント
- **左：月カレンダー（幅 60% → 約 502 px）**  
  - 月表示（6列×行）で**今日を太字＋濃い塗り**。日付フォント **18–22 px**。  
- **右：イベント一覧（幅 40% → 約 334 px）**  
  - 1行あたり **36–44 px**、アイコン＋短文（最大3行表示）。重要イベントは濃い背景で強調。

---

### フォント・階調・視認性（電子ペーパー最適化）
- **階調想定**：4段階（黒 / 濃灰 / 中灰 / 薄灰）を基準に設計。  
- **フォント**：日本語は **Noto Sans JP**、数値は **等幅（Noto Sans Mono JP）**。  
- **推奨フォントサイズ（px）**：時刻 140; 主要数値 48–64; ラベル 16–20; カレンダー日付 18–22。  
- **警告表現**：色不可のため **ハッチ（斜線）＋太枠＋アイコン**。  
- **コントラスト**：主要数値は背景と明確な濃淡差（黒寄り）を確保。

---

### 実装上の注意（Kindle / 電子ペーパー向け）
- **セーフエリア厳守**：重要な数値・アラートは Y ≤ 1302 px に収める。下側145 px（Y=1303..1447）は見切れ想定。  
- **更新**：10分毎の**平均値**を受け取り、**部分更新**で差分のみ描画。ゴースト対策で6–12時間に1回フルリフレッシュ。  
- **レンダリング**：**SVGで描画 → ラスタ化**して送るとシャープ。線幅は実機で確認。  
- **省電力**：数値が変わらない場合は更新スキップ。アニメーションは使わない。  

---

### ワイヤーフレーム（Kindle Gen10 6インチ 300ppi 向け SVG）

以下は **1072×1448 px** キャンバス、セーフエリア上から **1303 px**（下145px見切れ）を想定したワイヤーフレームSVGです。16階調の灰色を想定した塗り分け、主要要素に `id` を付与しています。編集しやすいように要素は矩形＋ラベルで表現しています。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1072" height="1448" viewBox="0 0 1072 1448" role="img" aria-label="E-paper monitor wireframe">
  <defs>
    <!-- 16-step greys (approx hex values) -->
    <style type="text/css"><![CDATA[
      .g0 { fill:#000000; }
      .g1 { fill:#111111; }
      .g2 { fill:#222222; }
      .g3 { fill:#333333; }
      .g4 { fill:#444444; }
      .g5 { fill:#555555; }
      .g6 { fill:#666666; }
      .g7 { fill:#777777; }
      .g8 { fill:#888888; }
      .g9 { fill:#999999; }
      .g10 { fill:#AAAAAA; }
      .g11 { fill:#BBBBBB; }
      .g12 { fill:#CCCCCC; }
      .g13 { fill:#DDDDDD; }
      .g14 { fill:#EEEEEE; }
      .g15 { fill:#F7F7F7; }
      .stroke { stroke:#222222; stroke-width:2; fill:none; }
      .thin { stroke:#444444; stroke-width:1.5; fill:none; stroke-dasharray:4 4; }
      .label { fill:#666666; font-family: 'Noto Sans JP', 'Noto Sans', 'sans-serif'; font-size:16px; }
      .num { fill:#000000; font-family: 'Noto Sans Mono JP', 'monospace'; font-weight:700; }
      .title { fill:#000000; font-family: 'Noto Sans JP', 'sans-serif'; font-weight:700; }
      .card { stroke:#333333; stroke-width:2; rx:8; ry:8; }
      .spark { stroke:#222222; stroke-width:2; fill:none; }
      .hatch { fill:url(#hatchPattern); }
    ]]></style>

    <!-- hatch pattern for clipped area -->
    <pattern id="hatchPattern" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
      <rect width="8" height="8" class="g15"/>
      <path d="M0 0 L0 8" stroke="#CCCCCC" stroke-width="1"/>
    </pattern>

    <!-- small sparkline sample polyline -->
    <g id="sparkSample">
      <polyline class="spark" points="0,18 10,12 20,16 30,8 40,14 50,10 60,12" />
    </g>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="1072" height="1448" class="g15" />

  <!-- Safe area boundary (top 1303px) -->
  <rect x="0" y="0" width="1072" height="1303" fill="none" class="thin" />

  <!-- Clipped / seen-off area (bottom 145px) -->
  <rect x="0" y="1303" width="1072" height="145" class="hatch" />

  <!-- Left navigation (id=left-nav) -->
  <g id="left-nav">
    <rect x="8" y="8" width="236" height="1303" class="g14" stroke="#222222" stroke-width="2" rx="6" ry="6"/>
    <!-- Top area: large time -->
    <g id="time-display">
      <rect x="16" y="16" width="220" height="365" class="g15 card" />
      <text x="124" y="120" text-anchor="middle" class="num" font-size="140">12:34</text>
      <text x="124" y="160" text-anchor="middle" class="label" font-size="24">06/21 (Sun)</text>
    </g>

    <!-- Middle: sensor cards -->
    <g id="sensors" transform="translate(16, 16 + 365 + 12)">
      <!-- layout: five cards stacked with 12px gap -->
      <!-- card 1: CPU % -->
      <g id="cpu-card">
        <rect x="0" y="0" width="204" height="110" class="g12 card" />
        <text x="8" y="30" class="label" font-size="14">CPU 使用率</text>
        <text x="8" y="70" class="num" font-size="48">41%</text>
        <g transform="translate(8,82)"><use href="#sparkSample" /></g>
      </g>

      <!-- card 2: CPU Temp -->
      <g id="cpu-temp" transform="translate(0,122)">
        <rect x="0" y="0" width="204" height="110" class="g12 card" />
        <text x="8" y="30" class="label" font-size="14">CPU 温度</text>
        <text x="8" y="70" class="num" font-size="48">41°C</text>
        <rect x="150" y="20" width="40" height="40" class="g6" stroke="#222222" stroke-width="2" rx="6" ry="6"/>
      </g>

      <!-- card 3: GPU -->
      <g id="gpu-card" transform="translate(0,244)">
        <rect x="0" y="0" width="204" height="110" class="g12 card" />
        <text x="8" y="30" class="label" font-size="14">GPU 使用率</text>
        <text x="8" y="70" class="num" font-size="48">0%</text>
        <g transform="translate(8,82)"><use href="#sparkSample" /></g>
      </g>

      <!-- card 4: Memory -->
      <g id="mem-card" transform="translate(0,366)">
        <rect x="0" y="0" width="204" height="110" class="g12 card" />
        <text x="8" y="30" class="label" font-size="14">メモリ使用率</text>
        <text x="8" y="70" class="num" font-size="48">62%</text>
        <g transform="translate(8,82)"><use href="#sparkSample" /></g>
      </g>

      <!-- card 5: Network -->
      <g id="net-card" transform="translate(0,488)">
        <rect x="0" y="0" width="204" height="110" class="g12 card" />
        <text x="8" y="30" class="label" font-size="14">ネットワーク</text>
        <text x="8" y="70" class="num" font-size="36">120 KB/s</text>
        <g transform="translate(8,92)"><use href="#sparkSample" /></g>
      </g>
    </g>

    <!-- Bottom: alert area -->
    <g id="alerts" transform="translate(16, 1042)">
      <rect x="0" y="0" width="204" height="240" class="g15 card" />
      <text x="8" y="28" class="label" font-size="16">アラート</text>
      <rect x="8" y="40" width="188" height="40" class="g10" stroke="#222222" stroke-width="2" rx="6" ry="6"/>
      <text x="16" y="68" class="label" font-size="14">なし</text>
    </g>
  </g>

  <!-- Main panel (id=main-panel) -->
  <g id="main-panel" transform="translate(260,8)">
    <!-- bounding box for main safe area -->
    <rect x="0" y="0" width="836" height="1303" class="g15" stroke="#222222" stroke-width="2" rx="6" ry="6"/>

    <!-- Top row: system summary and environment -->
    <g id="top-cards">
      <!-- left system summary (50%) -->
      <g id="system-summary" transform="translate(12,12)">
        <rect x="0" y="0" width="400" height="367" class="g13 card" />
        <text x="16" y="28" class="title" font-size="20">System Summary</text>
        <text x="16" y="80" class="label" font-size="14">CPU</text>
        <text x="120" y="80" class="num" font-size="48">41%</text>
        <text x="16" y="130" class="label" font-size="14">Temp</text>
        <text x="120" y="130" class="num" font-size="48">41°C</text>
        <text x="16" y="180" class="label" font-size="14">Memory</text>
        <text x="120" y="180" class="num" font-size="48">62%</text>
      </g>

      <!-- right environment card -->
      <g id="env-card" transform="translate(424,12)">
        <rect x="0" y="0" width="400" height="367" class="g13 card" />
        <text x="16" y="28" class="title" font-size="20">Environment</text>
        <text x="16" y="80" class="label" font-size="14">室温</text>
        <text x="120" y="80" class="num" font-size="48">29.0°C</text>
        <text x="16" y="130" class="label" font-size="14">湿度</text>
        <text x="120" y="130" class="num" font-size="48">30%</text>
        <text x="16" y="180" class="label" font-size="14">天気</text>
        <text x="120" y="180" class="label" font-size="18">曇一時雨</text>
        <text x="16" y="220" class="label" font-size="14">降水確率</text>
        <text x="120" y="220" class="num" font-size="36">10%</text>
      </g>
    </g>

    <!-- Middle: large area chart -->
    <g id="main-graph" transform="translate(12, 12 + 367 + 12)">
      <rect x="0" y="0" width="812" height="586" class="g15 card" />
      <text x="12" y="24" class="title" font-size="18">24h Trend (CPU %)</text>

      <!-- sample area chart: polyline + filled polygon -->
      <defs>
        <linearGradient id="areaGrad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#BBBBBB" stop-opacity="0.9"/>
          <stop offset="100%" stop-color="#EEEEEE" stop-opacity="0.6"/>
        </linearGradient>
      </defs>

      <!-- axes -->
      <line x1="40" y1="40" x2="40" y2="520" class="thin" />
      <line x1="40" y1="520" x2="780" y2="520" class="thin" />

      <!-- sample area polygon -->
      <polygon points="40,480 120,420 200,360 280,380 360,300 440,340 520,320 600,280 680,260 760,240 780,240 780,520 40,520"
               fill="url(#areaGrad)" stroke="#666666" stroke-width="2"/>

      <!-- threshold line -->
      <line x1="40" y1="300" x2="780" y2="300" stroke="#666666" stroke-dasharray="6 4" stroke-width="2"/>
      <text x="784" y="304" class="label" font-size="14">警告閾値 75%</text>

      <!-- sparklines row under chart -->
      <g id="sparklines" transform="translate(12, 540)">
        <rect x="0" y="0" width="260" height="60" class="g15 card" />
        <text x="8" y="16" class="label" font-size="12">CPU</text>
        <g transform="translate(8,24)"><use href="#sparkSample" /></g>

        <rect x="276" y="0" width="260" height="60" class="g15 card" />
        <text x="284" y="16" class="label" font-size="12">GPU</text>
        <g transform="translate(284,24)"><use href="#sparkSample" /></g>

        <rect x="552" y="0" width="260" height="60" class="g15 card" />
        <text x="560" y="16" class="label" font-size="12">Network</text>
        <g transform="translate(560,24)"><use href="#sparkSample" /></g>
      </g>
    </g>

    <!-- Bottom: calendar and events -->
    <g id="bottom-area" transform="translate(12, 12 + 367 + 12 + 586 + 12)">
      <!-- left: calendar (60% width) -->
      <g id="calendar" transform="translate(0,0)">
        <rect x="0" y="0" width="486" height="326" class="g15 card" />
        <text x="12" y="24" class="title" font-size="18">2026-06</text>
        <!-- simple grid of dates (placeholder) -->
        <g transform="translate(12,40)" class="label" font-size="18">
          <!-- 7 columns x 5 rows -->
          <!-- row 1 -->
          <text x="0" y="0">1</text>
          <text x="70" y="0">2</text>
          <text x="140" y="0">3</text>
          <text x="210" y="0">4</text>
          <text x="280" y="0">5</text>
          <text x="350" y="0">6</text>
          <text x="420" y="0">7</text>
          <!-- row 2 -->
          <text x="0" y="40">8</text>
          <text x="70" y="40">9</text>
          <text x="140" y="40">10</text>
          <text x="210" y="40">11</text>
          <text x="280" y="40">12</text>
          <text x="350" y="40">13</text>
          <text x="420" y="40">14</text>
          <!-- row 3 -->
          <text x="0" y="80">15</text>
          <text x="70" y="80">16</text>
          <text x="140" y="80">17</text>
          <text x="210" y="80">18</text>
          <text x="280" y="80">19</text>
          <text x="350" y="80">20</text>
          <text x="420" y="80" font-weight="700">21</text>
          <!-- row 4 -->
          <text x="0" y="120">22</text>
          <text x="70" y="120">23</text>
          <text x="140" y="120">24</text>
          <text x="210" y="120">25</text>
          <text x="280" y="120">26</text>
          <text x="350" y="120">27</text>
          <text x="420" y="120">28</text>
          <!-- row 5 -->
          <text x="0" y="160">29</text>
          <text x="70" y="160">30</text>
        </g>
      </g>

      <!-- right: events (40% width) -->
      <g id="events" transform="translate(506,0)">
        <rect x="0" y="0" width="294" height="326" class="g15 card" />
        <text x="12" y="24" class="title" font-size="18">Events</text>
        <g transform="translate(12,40)" class="label" font-size="16">
          <rect x="0" y="0" width="270" height="44" class="g11" stroke="#222222" stroke-width="1.5" rx="6" ry="6"/>
          <text x="12" y="28">08:30 会議 - 会議室A</text>

          <rect x="0" y="56" width="270" height="44" class="g15" stroke="#222222" stroke-width="1.5" rx="6" ry="6"/>
          <text x="12" y="84">13:00 レポート提出</text>

          <rect x="0" y="112" width="270" height="44" class="g15" stroke="#222222" stroke-width="1.5" rx="6" ry="6"/>
          <text x="12" y="140">18:00 定例ミーティング</text>
        </g>
      </g>
    </g>
  </g>

  <!-- Footer note about safe area -->
  <text x="12" y="1320" class="label" font-size="12">※ 下部145pxは見切れ領域です（セーフエリアは上1303px）</text>
</svg>
```
