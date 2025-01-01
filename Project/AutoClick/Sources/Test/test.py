import multiprocessing
import time
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

class SharedMemoryProcess(multiprocessing.Process):
    def __init__(self, shared_value):
        super().__init__()
        self.shared_value = shared_value

    def run(self):
        # Multiprocessingで共有メモリの値を変更する
        while True:
            with self.shared_value.get_lock():
                self.shared_value.value += 1
            print("Shared value:", self.shared_value.value)
            # 1秒ごとに値を更新
            time.sleep(1)

class MyKivyApp(App):
    def build(self):
        # 共有メモリの作成
        shared_value = multiprocessing.Value('i', 0)
        
        # Multiprocessingプロセスの開始
        process = SharedMemoryProcess(shared_value)
        process.start()

        # GUIの定義
        layout = BoxLayout(orientation='vertical')
        self.label = Label(text='Shared Memory Value: 0')
        layout.add_widget(self.label)

        # 1秒ごとに共有メモリの値をGUIに更新
        Clock.schedule_interval(lambda dt: self.update_label(shared_value), 1)

        return layout

    def update_label(self, shared_value):
        with shared_value.get_lock():
            self.label.text = f'Shared Memory Value: {shared_value.value}'

if __name__ == '__main__':
    MyKivyApp().run()
