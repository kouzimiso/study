import logging
import json
import datetime

# ログを格納するリスト
logs = []

# ログをリストに追加する関数
def log_append( message,level= logging.INFO):
    log = {'time': str(datetime.datetime.now()), 'level': level, 'message': message}
    logs.append(log)

# ログをファイルに書き込む関数
def log_write(file_path, level):
    # ログを指定のレベルでフィルタリング
    filtered_logs = [log for log in logs if logging.getLevelName(log['level']) >= logging.getLevelName(logging.getLogger().level)]

    # JSON文字列に変換
    logs_json = [json.dumps(log) for log in filtered_logs]

    # ファイルに追記
    with open(file_path, 'a') as f:
        for log_json in logs_json:
            f.write(log_json + '\n')

from multiprocessing import Process, Manager
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

def kivy_app_process(data_dict):
    class MyApp(App):
        def build(self):
            layout = BoxLayout(orientation='vertical')
            button = Button(text='Click me')
            button.bind(on_press=lambda x: self.update_data(data_dict))
            layout.add_widget(button)
            return layout

        def update_data(self, data_dict):
            data_dict['count'] += 1
            print(f"Data updated: {data_dict}")

    MyApp().run()

if __name__ == '__main__':
    with Manager() as manager:
        data_dict = manager.dict({'count': 0})
        p = Process(target=kivy_app_process, args=(data_dict,))
        p.start()
        p.join()
        print(f"Final data: {data_dict}")
    # ログをクリア
    logs.clear()

# ログの追加
def append_log(level, message):
    log = {
        'level': level,
        'message': message,
        'time': logging.Formatter().formatTime(logging.LogRecord(None, None, '', 0, message, None, None))
    }
    logs.append(log)



log_append('This is a debug message',logging.DEBUG)
log_append('This is a warning message',logging.WARNING)
log_write('myapp.log', logging.DEBUG)
