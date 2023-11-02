import os
import logging
import json
import datetime

# ログのリスト
log_list = []

# ログをリストに追加する関数
def log_append(msg, level):
    now = datetime.datetime.now()
    log_dict = {
        "time": now.strftime('%Y-%m-%d %H:%M:%S'),
        "msg": msg,
        "level": level
    }
    log_list.append(log_dict)

# ログをファイルに書き込む関数
def log_write(log_file_path, level=logging.INFO):
    with open(log_file_path, 'a') as f:
        for log in log_list:
            if log['level'] >= level:
                f.write(json.dumps(log) + "\n")
    # リストを空にする
    log_list.clear()

# Logging設定
def configure_logging(config_file_path):
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)

# ログ出力の例
def main():
    configure_logging('logging_config.json')
    logging.info('This is an info message')
    logging.error('This is an error message')
    log_append('This is a debug message', logging.DEBUG)
    log_append('This is a warning message', logging.WARNING)
    log_write('myapp.log', logging.DEBUG)

if __name__ == '__main__':
    main()
