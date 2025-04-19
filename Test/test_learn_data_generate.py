import random
import json
from datetime import datetime, timedelta

def generate_date_range():
    while True:
        try:
            start_date = datetime(random.randint(0, 3000), random.randint(1, 12), random.randint(1, 31)) 
            break
        except ValueError:
            continue

    end_date = start_date + timedelta(days=random.randint(1, 2))
    return f"{start_date.strftime('%Y/%m/%d')}～{end_date.strftime('%Y/%m/%d')}"

def generate_day_range():
    days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    start_day = random.choice(days)
    end_day = random.choice(days)
    return f"{start_day}～{end_day}"

def generate_time_range():
    start_hour = random.randint(0, 23)
    start_minute = random.randint(0, 59)
    end_hour = random.randint(start_hour, 23)
    end_minute = random.randint(0, 59)
    return f"{start_hour:02}:{start_minute:02}～{end_hour:02}:{end_minute:02}"

def generate_datetime():
    while True:
        try:
            date = datetime(
                random.randint(0, 3000), 
                random.randint(1, 12), 
                random.randint(1, 31),  # Use 28 to avoid invalid days
                random.randint(0, 23), 
                random.randint(0, 59)
            )
            return date.strftime('%Y/%m/%d %H:%M')
        except ValueError:
            continue

def is_within_date_range(condition, dt):
    try:
        start_str, end_str = condition.split('～')
        start_date = datetime.strptime(start_str.strip(), '%Y/%m/%d')
        end_date = datetime.strptime(end_str.strip(), '%Y/%m/%d')
        return start_date <= dt <= end_date
    except ValueError:
        return False

def is_within_day_range(condition, dt):
    day_mapping = {"月曜日": 0, "火曜日": 1, "水曜日": 2, "木曜日": 3, "金曜日": 4, "土曜日": 5, "日曜日": 6}
    try:
        start_day, end_day = condition.split('～')
        start_idx = day_mapping[start_day.strip()]
        end_idx = day_mapping[end_day.strip()]
        current_day_idx = dt.weekday()
        if start_idx <= end_idx:
            return start_idx <= current_day_idx <= end_idx
        else:  # handle wrap around week
            return current_day_idx >= start_idx or current_day_idx <= end_idx
    except KeyError:
        return False

def is_within_time_range(condition, dt):
    try:
        start_str, end_str = condition.split('～')
        start_time = datetime.strptime(start_str.strip(), '%H:%M').time()
        end_time = datetime.strptime(end_str.strip(), '%H:%M').time()
        current_time = dt.time()
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:  # handle wrap around midnight
            return current_time >= start_time or current_time <= end_time
    except ValueError:
        return False

def determine_result(condition, datetime_str):
    dt = datetime.strptime(datetime_str, '%Y/%m/%d %H:%M')
    if '～' in condition:
        if '/' in condition:
            return is_within_date_range(condition, dt)
        elif '曜' in condition:
            return is_within_day_range(condition, dt)
        else:
            return is_within_time_range(condition, dt)
    return False

def generate_data(n):
    data = []
    for _ in range(n):
        condition_type = random.choice(['date_range', 'day_range', 'time_range'])
        if condition_type == 'date_range':
            condition = generate_date_range()
        elif condition_type == 'day_range':
            condition = generate_day_range()
        else:
            condition = generate_time_range()
        
        datetime_str = generate_datetime()
        result = determine_result(condition, datetime_str)
        
        data.append({
            "condition": condition,
            "datetime": datetime_str,
            "result_value": result
        })
    return data


def append_data_to_file(data, file_path):
    # 既存のデータを読み込む
    with open(file_path, "r", encoding="utf-8") as f:
        source_data = json.load(f)

    # 既存のデータと新しいデータを結合
    all_data = source_data + data
    all_data = remove_duplicate_dicts(all_data)
    # ファイルにデータを書き込む
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False)


def remove_duplicate_dicts(data):
    unique_dicts = []
    seen_dicts = set()  # 重複をチェックするためのセット
    for d in data:
        # 辞書のアイテムをタプルに変換してセットに追加
        dict_items = tuple(sorted(d.items()))
        if dict_items not in seen_dicts:
            unique_dicts.append(d)
            seen_dicts.add(dict_items)
    return unique_dicts

# Generate 1000 data points
data = generate_data(1000)

# Print data as JSON string
print(json.dumps(data, indent=4, ensure_ascii=False))
# ファイルにデータを追記
file_path = "./Sources/Models/train_data.json"
append_data_to_file(data, file_path)