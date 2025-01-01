import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from multiprocessing import Process
import time
import sys
# ローカルモジュールをインポート
sys.path.append("../Common")
sys.path.append("../Models")
sys.path.append("../ViewModels")
sys.path.append("../Views")
sys.path.append("./Common")
sys.path.append("./Models")
sys.path.append("./ViewModels")
sys.path.append("./Views")
sys.path.append("./Sources/Common")
sys.path.append("./Sources/Models")
sys.path.append("./Sources/ViewModels")
sys.path.append("./Sources/Views")

# マルチプロセスで実行する関数
def background_task():
    for i in range(5):
        print(f"Background task running: {i}")
        time.sleep(1)

# KivyのGUIアプリケーションクラス
class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        button = Button(text='Start Background Task', size_hint=(1, 0.2))
        button.bind(on_press=self.start_process)
        layout.add_widget(button)
        return layout

    def start_process(self, instance):
        # マルチプロセスを起動
        p = Process(target=background_task)
        p.start()

if __name__ == '__main__':
    MyApp().run()
