#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle Monitor - Enhanced with temperature trends and improved API display
Paperwhite Gen.5 (768×1024, 213ppi)

新機能:
- CPU/GPU温度トレンドグラフを追加（CPU グラフの下）
- API表示の拡充（使用率を明確に表示）
- データ履歴に温度も記録
"""

import sys
import os
import datetime
import logging
import requests
import paramiko
import jpholiday
import json
import subprocess
import psutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import calendar
import yaml
from collections import deque

def load_config(config_file='config.yaml'):
    config_path = Path(config_file)
    if not config_path.exists():
        print("ERROR: Config file not found: " + config_file)
        sys.exit(1)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

CONFIG = load_config()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# データ履歴に温度も追加
DATA_HISTORY = {
    'cpu_pct': deque(maxlen=144),
    'gpu_pct': deque(maxlen=144),
    'cpu_temp': deque(maxlen=144),
    'gpu_temp': deque(maxlen=144),
    'timestamps': deque(maxlen=144)
}
DATA_FILE = Path.home() / '.kindle_monitor_data.json'

def load_data_history():
    global DATA_HISTORY
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                DATA_HISTORY['cpu_pct'] = deque(data.get('cpu_pct', []), maxlen=144)
                DATA_HISTORY['gpu_pct'] = deque(data.get('gpu_pct', []), maxlen=144)
                DATA_HISTORY['cpu_temp'] = deque(data.get('cpu_temp', []), maxlen=144)
                DATA_HISTORY['gpu_temp'] = deque(data.get('gpu_temp', []), maxlen=144)
    except Exception as e:
        logging.warning("Failed to load data history: " + str(e))

def save_data_history():
    try:
        data = {
            'cpu_pct': list(DATA_HISTORY['cpu_pct']),
            'gpu_pct': list(DATA_HISTORY['gpu_pct']),
            'cpu_temp': list(DATA_HISTORY['cpu_temp']),
            'gpu_temp': list(DATA_HISTORY['gpu_temp']),
            'last_update': datetime.datetime.now().isoformat()
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logging.warning("Failed to save data history: " + str(e))

# Data collection
def get_wio_link_data():
    try:
        wio = CONFIG['sensors']['wio_link']
        base = wio['base_url']
        sensor = wio['sensor']
        node_id = sensor['node_id']
        token = sensor['access_token']
        temp_key = sensor.get('temp_key', 'celsius_degree')
        humi_key = sensor.get('humi_key', 'humidity')

        temp_url = base + '/' + node_id + '/temperature?access_token=' + token
        temp_resp = requests.get(temp_url, timeout=5)
        temperature = temp_resp.json().get(temp_key, 0)

        humi_url = base + '/' + node_id + '/humidity?access_token=' + token
        humi_resp = requests.get(humi_url, timeout=5)
        humidity = humi_resp.json().get(humi_key, 0)

        return {'temp': temperature, 'humi': humidity}
    except Exception as e:
        logging.warning("Wio Link error: " + str(e))
        return {'temp': 0, 'humi': 0}

def get_weather_data():
    try:
        weather = CONFIG['sensors']['weather']
        url = weather['api_url'] + '?city=' + weather['city_code']
        resp = requests.get(url, timeout=5)
        data = resp.json()

        description = data.get('description', {}).get('text', '')
        forecasts = data.get('forecasts', [])

        # 今日と明日のデータを取得
        today = {'telop': '', 'image_url': '', 'image_pil': None, 'rain': '--'}
        tomorrow = {'telop': '', 'image_url': '', 'image_pil': None, 'rain': '--'}

        if len(forecasts) > 0:
            today['telop'] = forecasts[0].get('telop', '')
            today['rain'] = forecasts[0].get('chanceOfRain', {}).get('T18_24', '--')
            today['image_url'] = forecasts[0].get('image', {}).get('url', '')
            # SVG をダウンロード
            if today['image_url']:
                try:
                    img_resp = requests.get(today['image_url'], timeout=5)
                    if img_resp.status_code == 200:
                        from io import BytesIO
                        from PIL import Image as PILImage
                        today['image_pil'] = PILImage.open(BytesIO(img_resp.content)).convert('L').resize((40, 30))
                except:
                    pass

        if len(forecasts) > 1:
            tomorrow['telop'] = forecasts[1].get('telop', '')
            tomorrow['rain'] = forecasts[1].get('chanceOfRain', {}).get('T18_24', '--')
            tomorrow['image_url'] = forecasts[1].get('image', {}).get('url', '')
            # SVG をダウンロード
            if tomorrow['image_url']:
                try:
                    img_resp = requests.get(tomorrow['image_url'], timeout=5)
                    if img_resp.status_code == 200:
                        from io import BytesIO
                        from PIL import Image as PILImage
                        tomorrow['image_pil'] = PILImage.open(BytesIO(img_resp.content)).convert('L').resize((40, 30))
                except:
                    pass

        return {
            'description': description,
            'today': today,
            'tomorrow': tomorrow,
            'telop': today['telop'],
            'rain': today['rain']
        }
    except Exception as e:
        logging.warning("Weather error: " + str(e))
        return {
            'description': '',
            'today': {'telop': '', 'image_url': '', 'image_pil': None, 'rain': '--'},
            'tomorrow': {'telop': '', 'image_url': '', 'image_pil': None, 'rain': '--'},
            'telop': '',
            'rain': '--'
        }

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            return int(sum(t.current for t in temps['coretemp']) / len(temps['coretemp']))
        elif 'k10temp' in temps:
            return int(temps['k10temp'][0].current)
        for entries in temps.values():
            if entries:
                return int(entries[0].current)
        return 0
    except:
        return 0

def get_cpu_usage():
    try:
        return str(int(psutil.cpu_percent(interval=0.1)))
    except:
        return '--'

def get_gpu_usage():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader'],
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip().split('\n')[0].replace('%', '').strip() if result.returncode == 0 else '--'
    except:
        return '--'

def get_gpu_temp():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, timeout=5)
        return int(float(result.stdout.strip().split('\n')[0])) if result.returncode == 0 else 0
    except:
        return 0

def get_memory_usage():
    try:
        return str(int(psutil.virtual_memory().percent))
    except:
        return '--'

CLAUDE_CREDENTIALS_PATH = Path.home() / '.claude' / '.credentials.json'

def get_claude_oauth_token():
    """Claude Code の OAuth トークン (user:profile スコープ付き) を読み込む。
    期限切れの場合は None を返す。
    """
    try:
        if not CLAUDE_CREDENTIALS_PATH.exists():
            return None, 'no_credentials'
        with open(CLAUDE_CREDENTIALS_PATH, 'r') as f:
            creds = json.load(f)
        oauth = creds.get('claudeAiOauth', {})
        access_token = oauth.get('accessToken')
        expires_at_ms = oauth.get('expiresAt', 0)
        if not access_token:
            return None, 'no_token'
        # expiresAt はミリ秒
        now_ms = int(datetime.datetime.now().timestamp() * 1000)
        if expires_at_ms and now_ms >= expires_at_ms:
            return None, 'expired'
        return access_token, 'ok'
    except Exception as e:
        logging.warning("OAuth credentials read error: " + str(e))
        return None, 'read_error'

def get_storage_usage():
    """ストレージ使用率を取得。HOME のあるFSと /dev/sda3 を対象。"""
    result = {
        'home': {'label': 'Home', 'mount': '', 'used_pct': 0, 'used_gb': 0, 'total_gb': 0, 'avail_gb': 0},
        'sda3': {'label': 'Data', 'mount': '/dev/sda3', 'used_pct': 0, 'used_gb': 0, 'total_gb': 0, 'avail_gb': 0},
    }
    try:
        home_path = str(Path.home())
        for key, target in [('home', home_path), ('sda3', '/dev/sda3')]:
            try:
                if key == 'sda3':
                    # /dev/sda3 のマウントポイントを取得
                    mount_result = subprocess.run(
                        ['findmnt', '-n', '-o', 'TARGET', '/dev/sda3'],
                        capture_output=True, text=True, timeout=3
                    )
                    if mount_result.returncode != 0:
                        continue
                    target = mount_result.stdout.strip()
                    if not target:
                        continue

                usage = psutil.disk_usage(target)
                result[key]['mount'] = target
                result[key]['used_pct'] = int(usage.percent)
                result[key]['used_gb'] = int(usage.used / (1024**3))
                result[key]['total_gb'] = int(usage.total / (1024**3))
                result[key]['avail_gb'] = int(usage.free / (1024**3))
            except Exception as e:
                logging.warning("Storage " + key + " error: " + str(e))
    except Exception as e:
        logging.warning("Storage usage error: " + str(e))
    return result

def get_claude_usage():
    try:
        anthropic_cfg = CONFIG.get('anthropic', {})
        if not anthropic_cfg.get('enabled', False):
            return {'five_hour': '--', 'seven_day': '--', 'status': 'off'}

        # 優先: Claude Code OAuth credentials (user:profile スコープ持ち)
        token, token_status = get_claude_oauth_token()
        if token:
            headers = {
                'Authorization': 'Bearer ' + token,
                'anthropic-version': '2023-06-01',
                'anthropic-beta': 'oauth-2025-04-20',
                'Accept': 'application/json',
            }
        else:
            # フォールバック: 環境変数の API キー (スコープ不足の可能性あり)
            api_key = anthropic_cfg.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')
            if not api_key or api_key.startswith('sk-ant-...'):
                logging.warning("Claude usage: no credentials (oauth=" + token_status + ", env=missing)")
                return {'five_hour': '--', 'seven_day': '--', 'status': 'off'}
            if api_key.startswith('sk-ant-oat'):
                headers = {
                    'Authorization': 'Bearer ' + api_key,
                    'anthropic-version': '2023-06-01',
                    'anthropic-beta': 'oauth-2025-04-20',
                    'Accept': 'application/json',
                }
            else:
                headers = {
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'anthropic-beta': 'oauth-2025-04-20',
                    'Accept': 'application/json',
                }

        resp = requests.get('https://api.anthropic.com/api/oauth/usage', headers=headers, timeout=10)
        logging.info("Claude usage API: HTTP " + str(resp.status_code))

        if resp.status_code == 200:
            data = resp.json()
            fh = data.get('five_hour', {})
            sd = data.get('seven_day', {})
            return {
                'five_hour': str(int(fh.get('utilization', 0))) + '%',
                'seven_day': str(int(sd.get('utilization', 0))) + '%',
                'status': 'ok'
            }
        elif resp.status_code == 429:
            return {'five_hour': '--', 'seven_day': '--', 'status': '429'}
        elif resp.status_code == 401:
            return {'five_hour': '--', 'seven_day': '--', 'status': '401'}
        elif resp.status_code == 403:
            logging.warning("Claude usage 403: " + resp.text[:200])
            return {'five_hour': '--', 'seven_day': '--', 'status': '403'}
        else:
            logging.warning("Claude usage error " + str(resp.status_code) + ": " + resp.text[:200])
            return {'five_hour': '--', 'seven_day': '--', 'status': 'error'}
    except Exception as e:
        logging.warning("Claude usage exception: " + str(e))
        return {'five_hour': '--', 'seven_day': '--', 'status': 'error'}

def record_data_point(cpu_pct, gpu_pct, cpu_temp, gpu_temp):
    DATA_HISTORY['cpu_pct'].append(int(cpu_pct.rstrip('%') or '0'))
    DATA_HISTORY['gpu_pct'].append(int(gpu_pct.rstrip('%') or '0'))
    DATA_HISTORY['cpu_temp'].append(cpu_temp)
    DATA_HISTORY['gpu_temp'].append(gpu_temp)
    DATA_HISTORY['timestamps'].append(datetime.datetime.now())

def draw_donut(draw, cx, cy, r_outer, r_inner, percent, fill_color=80, bg_color=210, outline_color=100):
    """ドーナツチャート描画。percent: 0-100 (str/int)、中央は透明（背景色）。"""
    try:
        pct = float(str(percent).rstrip('%')) if percent not in (None, '--', '') else 0
    except (ValueError, TypeError):
        pct = 0
    pct = max(0, min(100, pct))

    bbox_outer = [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer]
    bbox_inner = [cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner]

    # 背景リング（未使用部分）
    draw.ellipse(bbox_outer, fill=bg_color, outline=outline_color, width=1)

    # 使用率の円弧（12時方向から時計回り）
    if pct > 0:
        start_angle = -90
        end_angle = -90 + (pct / 100) * 360
        draw.pieslice(bbox_outer, start=start_angle, end=end_angle, fill=fill_color, outline=outline_color, width=1)

    # 中央の穴
    draw.ellipse(bbox_inner, fill=255, outline=outline_color, width=1)

def draw_grid_25(draw, x, y, width, height, max_val=100, font=None, label_left=True):
    """25%刻みのグリッド線と目盛ラベルを描画"""
    for i in range(5):  # 0, 25, 50, 75, 100
        ratio = i / 4
        gy = y + height - height * ratio
        # 横線（点線風: 短い線を連続描画）
        if i == 0 or i == 4:
            draw.line([(x, gy), (x + width, gy)], fill=80, width=1)
        else:
            # 点線
            dash_w = 4
            gap_w = 4
            cx = x
            while cx < x + width:
                draw.line([(cx, gy), (min(cx + dash_w, x + width), gy)], fill=160, width=1)
                cx += dash_w + gap_w
        # 目盛ラベル
        if font:
            label = str(int(max_val * ratio))
            if label_left:
                draw.text((x - 4, gy), label, fill=80, font=font, anchor='rm')
            else:
                draw.text((x + width + 4, gy), label, fill=80, font=font, anchor='lm')

def draw_area_graph(draw, x, y, width, height, data, color_fill=200, max_val=None):
    if not data or len(data) < 2:
        return
    if max_val is None:
        max_val = max(data) if data else 1
        if max_val == 0:
            max_val = 1

    points = []
    step = width / (len(data) - 1) if len(data) > 1 else 0
    for i, val in enumerate(data):
        px = x + i * step
        py = y + height - (val / max_val) * height
        points.append((px, py))

    if len(points) >= 2:
        poly_points = [points[0]] + points + [(x + width, y + height), (x, y + height)]
        draw.polygon(poly_points, fill=color_fill, outline=0)

    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=0, width=2)

def wrap_japanese_text(text, max_chars_per_line, max_lines=None):
    """日本語テキストを指定文字数でラップ"""
    text = text.replace('　', ' ').strip()  # 全角スペースを半角に
    lines = []
    # 改行で分割しつつ、長すぎる行は文字数で折り返す
    for paragraph in text.split('\n'):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        while len(paragraph) > max_chars_per_line:
            lines.append(paragraph[:max_chars_per_line])
            paragraph = paragraph[max_chars_per_line:]
            if max_lines and len(lines) >= max_lines:
                return lines
        if paragraph:
            lines.append(paragraph)
            if max_lines and len(lines) >= max_lines:
                return lines
    return lines

# Create image
def create_image():
    width = 768
    height = 1024
    safe_height = int(height * 0.90)
    img = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_path_cjk = '/usr/share/fonts/opentype/noto/'
    font_path_mono = '/usr/share/fonts/truetype/dejavu/'

    font_time_large = ImageFont.truetype(font_path_mono + 'DejaVuSansMono-Bold.ttf', 72)
    font_label = ImageFont.truetype(font_path_cjk + 'NotoSansCJK-Regular.ttc', 16)
    font_label_en = ImageFont.truetype(font_path_mono + 'DejaVuSansMono.ttf', 16)
    font_value = ImageFont.truetype(font_path_mono + 'DejaVuSansMono-Bold.ttf', 32)
    font_value_small = ImageFont.truetype(font_path_mono + 'DejaVuSansMono-Bold.ttf', 24)
    font_date = ImageFont.truetype(font_path_cjk + 'NotoSansCJK-Regular.ttc', 14)
    font_cal_day = ImageFont.truetype(font_path_mono + 'DejaVuSansMono.ttf', 18)
    font_cal_num = ImageFont.truetype(font_path_mono + 'DejaVuSansMono.ttf', 22)
    font_small = ImageFont.truetype(font_path_mono + 'DejaVuSansMono.ttf', 12)
    font_label_jp = ImageFont.truetype(font_path_cjk + 'NotoSansCJK-Bold.ttc', 16)
    font_desc_jp = ImageFont.truetype(font_path_cjk + 'NotoSansCJK-Regular.ttc', 13)
    font_scale = ImageFont.truetype(font_path_mono + 'DejaVuSansMono.ttf', 10)

    # Get data
    sensor = get_wio_link_data()
    weather = get_weather_data()
    cpu_pct = get_cpu_usage()
    cpu_temp = get_cpu_temp()
    gpu_pct = get_gpu_usage()
    gpu_temp = get_gpu_temp()
    mem_pct = get_memory_usage()
    storage = get_storage_usage()
    now = datetime.datetime.now()

    record_data_point(cpu_pct, gpu_pct, cpu_temp, gpu_temp)

    left_nav_x = 4
    left_nav_w = 246
    left_nav_pad = 12

    main_x = left_nav_x + left_nav_w + 4
    main_w = width - main_x - 4
    main_pad = 12

    # --- LEFT NAVIGATION ---
    top_margin = 16
    y_pos = top_margin

    # 時刻
    draw.text((left_nav_x + left_nav_w // 2, y_pos + 28),
             now.strftime('%H:%M'), fill=0, font=font_time_large, anchor='mm')

    # 日付（行間を広げ、font_label_jp と同じサイズに）
    y_pos += 72
    weekday_jp = ['月', '火', '水', '木', '金', '土', '日'][now.weekday()]
    draw.text((left_nav_x + left_nav_w // 2, y_pos),
             now.strftime('%m/%d') + ' (' + weekday_jp + ')',
             fill=0, font=font_label_jp, anchor='mm')

    y_pos += 32
    card_h = 58
    card_pad = 12

    for label, value in [('CPU%', cpu_pct), ('CPU°C', str(cpu_temp)), ('GPU%', gpu_pct), ('Mem%', mem_pct)]:
        card_x = left_nav_x + 4
        card_w = left_nav_w - 8

        draw.rectangle([card_x, y_pos, card_x + card_w, y_pos + card_h],
                       outline=100, width=1, fill=235)

        draw.text((card_x + card_pad, y_pos + 12), label, fill=100, font=font_label_en)
        draw.text((card_x + card_w - card_pad, y_pos + 12), value, fill=0, font=font_value_small, anchor='ra')

        y_pos += card_h + 8

    # 天気予報エリア
    weather_h = safe_height - y_pos - 8
    if weather_h > 100:
        weather_x = left_nav_x + 4
        weather_w = left_nav_w - 8

        draw.rectangle([weather_x, y_pos, weather_x + weather_w, y_pos + weather_h],
                       outline=100, width=1, fill=240)

        draw.text((weather_x + card_pad, y_pos + 6), '天気予報', fill=80, font=font_label_jp)

        # 今日の天気（テキスト表記）
        y_offset = 32
        draw.text((weather_x + card_pad, y_pos + y_offset), '今日:', fill=100, font=font_label_jp)
        today_text = weather['today']['telop'] if weather['today']['telop'] else '--'
        draw.text((weather_x + card_pad + 56, y_pos + y_offset), today_text, fill=0, font=font_label_jp)

        # 明日の天気（テキスト表記）
        y_offset += 26
        draw.text((weather_x + card_pad, y_pos + y_offset), '明日:', fill=100, font=font_label_jp)
        tomorrow_text = weather['tomorrow']['telop'] if weather['tomorrow']['telop'] else '--'
        draw.text((weather_x + card_pad + 56, y_pos + y_offset), tomorrow_text, fill=0, font=font_label_jp)

        # 区切り線
        y_offset += 28
        draw.line([(weather_x + card_pad, y_pos + y_offset),
                   (weather_x + weather_w - card_pad, y_pos + y_offset)],
                  fill=180, width=1)

        # テキスト説明（全文表示、日本語対応）
        y_offset += 8
        if weather['description']:
            # 利用可能な高さから最大行数を計算
            available_h = weather_h - y_offset - 8
            line_height = 18
            max_lines = max(1, available_h // line_height)
            # 1行あたり最大文字数（パネル幅に合わせて、左右余白を均等に）
            max_chars = 17
            wrapped_lines = wrap_japanese_text(weather['description'], max_chars, max_lines=max_lines)
            for line in wrapped_lines:
                draw.text((weather_x + card_pad, y_pos + y_offset), line, fill=40, font=font_desc_jp)
                y_offset += line_height

    # --- MAIN PANEL ---
    main_y = top_margin

    # 上段: Environment + API
    card_h = 160
    card_pad = 12
    env_x = main_x + 4
    env_w = (main_w - 12) // 2

    # Environment カード
    draw.rectangle([env_x, main_y, env_x + env_w, main_y + card_h],
                   outline=100, width=1, fill=235)
    draw.text((env_x + card_pad, main_y + 8), 'Environment', fill=80, font=font_label_en)

    y_offset = 32
    for label, value in [('Temp:', str(round(sensor['temp'], 1)) + '°C'),
                         ('Humi:', str(int(sensor['humi'])) + '%'),
                         ('Rain:', weather['rain'])]:
        draw.text((env_x + card_pad, main_y + y_offset), label, fill=100, font=font_label_en)
        draw.text((env_x + env_w - card_pad, main_y + y_offset), value, fill=0, font=font_value_small, anchor='ra')
        y_offset += 36

    # Storage カード（ドーナツチャート: Home FS と /dev/sda3）
    stor_x = env_x + env_w + 4
    draw.rectangle([stor_x, main_y, stor_x + env_w, main_y + card_h],
                   outline=100, width=1, fill=235)
    draw.text((stor_x + card_pad, main_y + 8), 'Storage', fill=80, font=font_label_en)

    donut_r_outer = 36
    donut_r_inner = 23
    donut_y = main_y + 80
    col1_cx = stor_x + env_w // 4
    col2_cx = stor_x + env_w * 3 // 4

    font_donut_pct = ImageFont.truetype(font_path_mono + 'DejaVuSansMono-Bold.ttf', 16)
    font_donut_label = ImageFont.truetype(font_path_mono + 'DejaVuSansMono-Bold.ttf', 13)
    font_donut_sub = ImageFont.truetype(font_path_mono + 'DejaVuSansMono.ttf', 10)

    for cx, key in [(col1_cx, 'home'), (col2_cx, 'sda3')]:
        info = storage[key]
        pct = info['used_pct']
        # 使用率が高いほど濃い色
        fill_color = 60 if pct >= 90 else (80 if pct >= 75 else 100)
        draw_donut(draw, cx, donut_y, donut_r_outer, donut_r_inner,
                  pct, fill_color=fill_color, bg_color=215)
        draw.text((cx, donut_y), str(pct) + '%',
                 fill=0, font=font_donut_pct, anchor='mm')
        draw.text((cx, donut_y + donut_r_outer + 12), info['label'], fill=80,
                 font=font_donut_label, anchor='mm')
        # 空き容量サブテキスト
        if info['total_gb'] > 0:
            sub = str(info['avail_gb']) + 'G free'
            draw.text((cx, donut_y + donut_r_outer + 26), sub, fill=100,
                     font=font_donut_sub, anchor='mm')

    # CPU % グラフ（25%刻みの目盛付き）
    main_y += card_h + 12
    graph_h = 120
    graph_x = main_x + 4
    graph_w = main_w - 8

    draw.rectangle([graph_x, main_y, graph_x + graph_w, main_y + graph_h],
                   outline=100, width=1, fill=245)
    draw.text((graph_x + card_pad, main_y + 4), 'CPU % (24h)', fill=80, font=font_label_en)

    plot_x = graph_x + 32
    plot_w = graph_w - 48
    plot_y = main_y + 22
    plot_h = 88

    # Y軸とX軸
    draw.line([(plot_x, plot_y), (plot_x, plot_y + plot_h)], fill=80, width=1)
    draw.line([(plot_x, plot_y + plot_h), (plot_x + plot_w, plot_y + plot_h)], fill=80, width=1)

    # 25%刻みグリッド
    draw_grid_25(draw, plot_x, plot_y, plot_w, plot_h, max_val=100, font=font_scale, label_left=True)

    if len(DATA_HISTORY['cpu_pct']) > 1:
        draw_area_graph(draw, plot_x, plot_y, plot_w, plot_h,
                       list(DATA_HISTORY['cpu_pct']), color_fill=200, max_val=100)

    # CPU/GPU 温度グラフを左右2分割
    main_y += graph_h + 8
    temp_graph_h = 130
    temp_gap = 8
    temp_w = (graph_w - temp_gap) // 2

    # CPU 温度（左）
    cpu_temp_x = graph_x
    draw.rectangle([cpu_temp_x, main_y, cpu_temp_x + temp_w, main_y + temp_graph_h],
                   outline=100, width=1, fill=245)
    draw.text((cpu_temp_x + card_pad, main_y + 4), 'CPU Temp °C (24h)', fill=80, font=font_label_en)

    tp_x = cpu_temp_x + 32
    tp_w = temp_w - 48
    tp_y = main_y + 22
    tp_h = 95

    draw.line([(tp_x, tp_y), (tp_x, tp_y + tp_h)], fill=80, width=1)
    draw.line([(tp_x, tp_y + tp_h), (tp_x + tp_w, tp_y + tp_h)], fill=80, width=1)

    # 温度の25%刻みグリッド（0-100°C）
    draw_grid_25(draw, tp_x, tp_y, tp_w, tp_h, max_val=100, font=font_scale, label_left=True)

    if len(DATA_HISTORY['cpu_temp']) > 1:
        draw_area_graph(draw, tp_x, tp_y, tp_w, tp_h,
                       list(DATA_HISTORY['cpu_temp']), color_fill=180, max_val=100)

    # GPU 温度（右）
    gpu_temp_x = cpu_temp_x + temp_w + temp_gap
    draw.rectangle([gpu_temp_x, main_y, gpu_temp_x + temp_w, main_y + temp_graph_h],
                   outline=100, width=1, fill=245)
    draw.text((gpu_temp_x + card_pad, main_y + 4), 'GPU Temp °C (24h)', fill=80, font=font_label_en)

    tp_x = gpu_temp_x + 32
    tp_y = main_y + 22

    draw.line([(tp_x, tp_y), (tp_x, tp_y + tp_h)], fill=80, width=1)
    draw.line([(tp_x, tp_y + tp_h), (tp_x + tp_w, tp_y + tp_h)], fill=80, width=1)

    draw_grid_25(draw, tp_x, tp_y, tp_w, tp_h, max_val=100, font=font_scale, label_left=True)

    if len(DATA_HISTORY['gpu_temp']) > 1:
        draw_area_graph(draw, tp_x, tp_y, tp_w, tp_h,
                       list(DATA_HISTORY['gpu_temp']), color_fill=210, max_val=100)

    # トレンドグラフセクション全体の高さ更新
    main_y_addition = temp_graph_h

    # カレンダー
    main_y += temp_graph_h + 8
    cal_h = safe_height - main_y - 4
    cal_x = main_x + 4
    cal_w = main_w - 8

    draw.rectangle([cal_x, main_y, cal_x + cal_w, main_y + cal_h],
                   outline=100, width=1, fill=245)

    # 年-月ラベル拡大
    font_cal_title = ImageFont.truetype(font_path_mono + 'DejaVuSansMono-Bold.ttf', 28)
    draw.text((cal_x + card_pad, main_y + 8), now.strftime('%Y-%m'), fill=0, font=font_cal_title)

    cal = calendar.monthcalendar(now.year, now.month)
    cal_y = main_y + 56
    col_width = (cal_w - 8) // 7
    row_height = 36  # 行間を広く

    # 曜日ヘッダー（土＝Sat 灰、日＝Sun 灰）
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, day_name in enumerate(weekday_labels):
        # 土曜=index 5, 日曜=index 6
        wd_color = 120 if i >= 5 else 80
        draw.text((cal_x + 4 + i * col_width + col_width // 2, cal_y),
                 day_name, fill=wd_color, font=font_cal_day, anchor='mm')

    # ヘッダー下に区切り線
    cal_y += 18
    draw.line([(cal_x + 8, cal_y), (cal_x + cal_w - 8, cal_y)], fill=150, width=1)

    cal_y += row_height // 2 + 4
    for week in cal:
        for day_idx, day_num in enumerate(week):
            if day_num > 0:
                is_today = day_num == now.day
                is_holiday = jpholiday.is_holiday(datetime.date(now.year, now.month, day_num))
                is_weekend = day_idx >= 5  # 土日

                cell_x1 = cal_x + 4 + day_idx * col_width + 2
                cell_x2 = cal_x + 4 + day_idx * col_width + col_width - 2
                cell_y1 = cal_y - 16
                cell_y2 = cal_y + 14

                # 祝日: 背景塗りつぶし + 枠取り
                if is_holiday and not is_today:
                    draw.rectangle([cell_x1, cell_y1, cell_x2, cell_y2],
                                  outline=80, width=1, fill=210)

                # 今日: 濃い枠取り
                if is_today:
                    draw.rectangle([cell_x1, cell_y1, cell_x2, cell_y2],
                                  outline=0, width=2, fill=140)

                # 文字色: 今日=黒、祝日=黒（背景で識別）、土日=灰、平日=黒
                if is_today:
                    text_color = 0
                elif is_holiday:
                    text_color = 0
                elif is_weekend:
                    text_color = 120
                else:
                    text_color = 0

                draw.text((cal_x + 4 + day_idx * col_width + col_width // 2, cal_y),
                         str(day_num), fill=text_color, font=font_cal_num, anchor='mm')
        cal_y += row_height

    return img

# Upload to Kindle
def upload_to_kindle(img):
    try:
        temp_file = '/tmp/panel.png'
        img.save(temp_file, 'PNG')
        logging.info("Image saved: " + temp_file)

        kindle_cfg = CONFIG['kindle']
        ssh_cfg = kindle_cfg['ssh']
        kindle_ip = kindle_cfg['ip_address']

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(kindle_ip, port=ssh_cfg.get('port', 22),
                   username=ssh_cfg['username'],
                   password=ssh_cfg.get('password'),
                   timeout=ssh_cfg.get('timeout', 5))

        sftp = ssh.open_sftp()
        sftp.put(temp_file, kindle_cfg['sftp_target'])
        sftp.close()
        logging.info("Uploaded to Kindle")

        stdin, stdout, stderr = ssh.exec_command(kindle_cfg['display_command'])
        logging.info("Display command executed")

        ssh.close()
        return True
    except Exception as e:
        logging.error("Kindle upload error: " + str(e))
        return False

# Main
def main():
    try:
        logging.info("Starting Kindle display update (enhanced)")
        load_data_history()
        img = create_image()
        save_data_history()
        upload_to_kindle(img)
        logging.info("Complete")
    except Exception as e:
        logging.error("Error: " + str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
