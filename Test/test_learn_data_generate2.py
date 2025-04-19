import random
from datetime import datetime, timedelta
import json

def generate_data(n):
    data = []
    for _ in range(n):
        # パターン1: 特定の日時の時刻範囲と時刻の比較
        if random.choice([True, False]):
            while True:
                try:
                    start_time = datetime(random.randint(2000, 3000), random.randint(1, 12), random.randint(1, 31),
                                    random.randint(0, 23), random.randint(0, 59))
                    break
                except:
                    continue
            end_time = start_time + timedelta(hours=random.randint(1, 3))
            condition = f"{start_time.strftime('%Y/%m/%d %H:%M')}～{end_time.strftime('%Y/%m/%d %H:%M')}"
            datetime_str = f"{random.randint(0, 23):02}:{random.randint(0, 59):02}"
            result = start_time <= datetime.strptime(datetime_str, '%H:%M') <= end_time
        # パターン2: 時刻範囲と日時の比較
        else:
            start_time = timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            end_time = start_time + timedelta(hours=random.randint(1, 5))
            condition = f"{start_time.seconds // 3600:02}:{(start_time.seconds % 3600) // 60:02}～{end_time.seconds // 3600:02}:{(end_time.seconds % 3600) // 60:02}"
            while True:
                try:
                    datetime_obj = datetime(random.randint(1000, 3000), random.randint(1, 12), random.randint(1, 31),
                                    random.randint(0, 23), random.randint(0, 59))
                    break
                except:
                    continue

            datetime_str = datetime_obj.strftime('%Y/%m/%d %H:%M')
            result = datetime.strptime(condition.split('～')[0], '%H:%M').time() <= datetime_obj.time() <= datetime.strptime(condition.split('～')[1], '%H:%M').time()

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
        json.dump(all_data, f, indent=4, ensure_ascii=False)


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

# 生成するデータの数
n = 10000

# データの生成
data = generate_data(n)


# Print data as JSON string
print(json.dumps(data, indent=4, ensure_ascii=False))
# ファイルにデータを追記
file_path = "./Sources/Models/train_data.json"
append_data_to_file(data, file_path)


