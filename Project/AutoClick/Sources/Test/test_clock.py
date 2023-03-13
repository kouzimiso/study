import datetime

date_string = "2023-03-11 24:00:00"
date_format = "%Y-%m-%d %H:%M:%S"

# 文字列を年月日と時間に分解する
date_parts, time_parts = date_string.split(" ")

# 時間を":", "."で分解する
hour, minute, second = time_parts.split(":")

# datetimeオブジェクトを作成する
date_time = datetime.datetime.strptime(date_string, date_format)

# 時間が24:00の場合、時刻を23:59:59.999に変更する
if hour == "24" and minute == "00" and second == "00":
    date_time = date_time.replace(hour=23, minute=59, second=59, microsecond=999000)

# datetimeオブジェクトからtimeオブジェクトを作成する
time = date_time.time()

print(time)
