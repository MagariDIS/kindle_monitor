# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an IoT display project that renders sensor data and calendar information on a Kindle e-ink display. The script:
- Fetches real-time sensor data (temperature, humidity, CO2) from a local Node-RED server or weather API
- Generates a multi-panel image with power data, sensor readings, date/time, and calendar
- Transfers the image to a Kindle device via SSH/SFTP
- Updates the Kindle's screensaver display

## Architecture

### Main Flow
1. **Data Collection Layer**: `get_sensor_data_map()` and `get_power_data_map()` fetch sensor values from remote HTTP endpoints (either local InfluxDB via Node-RED or public weather API)
2. **Image Generation Layer**: Multiple panel classes compose and render data onto a PIL Image
   - `SenseLargeHeaderPanel`: Power/weather metrics (top section)
   - `SenseLargeFooterPanel`: Date and weekday (bottom section)
   - `SenseDetailPanel`: Detailed sensor readings (temperature, humidity, CO2 for multiple locations)
   - `UpdateTimePanel`: Last update timestamp
   - `drawCalendarClass`: Month calendar with holidays and events
3. **Device Communication Layer**: SSH connection to Kindle device to transfer image and execute display commands

### Key Classes

- **Panel Classes** (`SenseLargeHeaderPanel`, `SenseLargeFooterPanel`, `SenseDetailPanel`, `UpdateTimePanel`):
  - Each has `offset_map()` to calculate positions for text/icons
  - `draw()` method renders content and returns the next Y position for layout
  - Use numpy arrays for coordinate calculations
  - Use PIL for image drawing and fonts

- **drawCalendarClass**: 
  - Renders a full month calendar view
  - Highlights Japanese holidays (via jpholiday)
  - Shows upcoming events (currently hard-coded)

### Data Flow

```
Sensor APIs
   ↓
get_sensor_data_map() / get_power_data_map()
   ↓
Panel Classes (draw to PIL Image)
   ↓
SSH/SFTP to Kindle
   ↓
eips command to update e-ink display
```

## Dependencies

- **Core**: Python 3
- **Image Processing**: PIL (Pillow)
- **Data**: requests, numpy
- **SSH/SFTP**: paramiko
- **Date/Time**: datetime, iso8601, pytz, jpholiday (Japanese holidays)
- **Optional**: googleCalendar module (imported but commented out in usage)

## Configuration

### Key Paths (hardcoded - requires environment-specific updates)
- Icons: `/usr/share/icons/mate/48x48/` (calendar, power icons)
- Weather icons: `/home/tmagari/img/` (sunny.png, rainny.png)
- Fonts: `/usr/share/fonts/truetype/` (TakaoGothic, DejaVu)
- Temp panel: `/tmp/panel.png`

### Sensor Configuration
- `PLACE_LIST`: Locations to monitor (currently: `['リビング', '天気']`)
- `HOST_MAP`: Maps locations to hostnames (`'リビング': 'rasp-meter-1'`, `'天気': 'rasp-meter-2'`)
- Node-RED API: `http://10.0.1.14:1880/m5echo/query`
- Weather API: `https://weather.tsukumijima.net/api/forecast?city=270000`

### Kindle Configuration
- Discovery: Uses `netdiscover` to find Kindle by MAC (`f0:4f:7c:ee:3e:9f`)
- Fallback IP: `10.0.1.143`
- SSH credentials: `root`/`mario` (hardcoded - security risk)
- SFTP target: `/mnt/us/panel.png`
- Display command: `eips` utility on Kindle

## Running the Script

```bash
# Install dependencies
pip install PyYAML Pillow requests numpy paramiko jpholiday pytz iso8601

# Copy and configure
cp config.yaml.example config.yaml
# Edit config.yaml with your environment values

# Run the main script
python3 kindle_calendar.py

# Or run via cron (typically every 30 minutes)
# */30 * * * * cd /path/to/kindle_monitor && python3 kindle_calendar.py
```

## セキュリティ設定

### 1. sudo パスワード不要化（netdiscoverコマンド用）

cronジョブから実行する場合、sudoers を設定してパスワード入力を不要にします：

```bash
# sudoers ファイルを編集
sudo visudo

# 以下の行を追加（NOPASSWD により netdiscover がパスワード不要に）
username ALL=(ALL) NOPASSWD: /usr/bin/netdiscover

# 保存・終了して完了
```

### 2. SSH 鍵認証の設定（推奨）

Kindle への SSH 接続をパスワードから鍵認証に変更します：

**Step 1: Kindle 用の SSH 鍵ペアを生成**
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/kindle_id_rsa -N ""
# -N "" でパスフレーズなし（cron から自動実行するため）
```

**Step 2: 公開鍵を Kindle に転送**
```bash
# 初回のみパスワード認証で Kindle に接続
ssh-copy-id -i ~/.ssh/kindle_id_rsa.pub -p 22 root@10.0.1.143
# または手動で ~/.ssh/kindle_id_rsa.pub の内容を Kindle の ~/.ssh/authorized_keys に追加
```

**Step 3: config.yaml で秘密鍵パスを指定**
```yaml
kindle:
  ssh:
    private_key_path: "/home/tmagari/.ssh/kindle_id_rsa"
    password: null  # パスワード認証は不要
```

**Step 4: パスワード認証を無効化（Kindle 側・オプション）**
```bash
ssh root@10.0.1.143
# Kindle 上で以下を編集
vi /etc/ssh/sshd_config
# PasswordAuthentication no に変更
# sshd 再起動: /etc/init.d/sshd restart
```

### 3. Kindle での sudo/SSH 設定（初期セットアップ）

Kindle 上で SSH パスワード認証を許可する場合：
```bash
ssh root@10.0.1.143  # 初回はパスワード認証
# Kindle 上で実行：
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# 公開鍵を ~/.ssh/authorized_keys に追加
```

### 4. ログ管理

設定ファイルで logging を有効化すると、実行結果がファイルに記録されます：

```yaml
logging:
  enabled: true
  level: "INFO"
  file: "/var/log/kindle_calendar.log"
```

cronジョブでログを出力する場合の設定例：
```bash
*/30 * * * * cd /path/to/kindle_monitor && python3 kindle_calendar.py >> /var/log/kindle_calendar.log 2>&1
```

## Important Notes

### Hardcoded Values
- Kindle SSH password is hardcoded as `'mario'` (line 780) — **security concern for production**
- Image paths, font paths, and API endpoints are absolute paths/URLs specific to the developer's environment
- Panel dimensions (758×1024) are tuned for specific Kindle model

### Data Fetching Logic
- If `wionode_use` global exists: fetches from local InfluxDB via Node-RED
- Otherwise: falls back to public weather API (only returns limited weather data)
- Sensor data includes: temperature, humidity, CO2, min/max power values, last update time

### Panel Layout System
- Coordinates are calculated using numpy arrays for composition
- `offset_map()` methods generate absolute positions for all text elements
- `draw()` methods use PIL's `ImageDraw` and return the Y position of drawn content
- Next panel offset is based on previous panel's return value

### Font System
- `FONT_MAP`: Maps symbolic names to truetype file paths
- `FACE_MAP`: Maps face names to font type and size
- `get_font()` helper loads fonts on demand

### Display Updates
- Generates `/tmp/panel.png` image
- Also generates calendar view to same file (overwrites)
- Transfers to Kindle via SFTP
- Executes `eips` command to render (both main display and screensaver)

## Environment Considerations

- **Linux-only**: Uses system font paths, `netdiscover` command, and SSH
- **Network**: Requires connectivity to Kindle device and sensor APIs
- **Permissions**: May require sudo for `netdiscover` network scanning
- **Timezone**: Uses `pytz` for timezone handling; ensure system timezone is configured

## Potential Issues

1. **Hardcoded paths**: Will fail if fonts or icons not at expected locations
2. **Network dependency**: Requires reachable Kindle and sensor servers
3. **Credential exposure**: SSH password is plain text in code
4. **Image overwrite**: Calendar and sensor images both write to `/tmp/panel.png` (only one is visible)
5. **Commented code**: Tapo camera integration and `SenseDetailPanel` are commented out; may be incomplete
