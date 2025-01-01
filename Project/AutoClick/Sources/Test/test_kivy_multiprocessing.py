import sys
import queue
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from functools import partial

class MyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_queue = queue.Queue()
        self.worker_function()


    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.output_label = Label(text='Output will be displayed here')
        sys.stdout = self.output_label  # 標準出力をOutputLabelにリダイレクト
        layout.add_widget(self.output_label)
        Clock.schedule_interval(self.update_output, 1)  # 出力の更新を定期的に行う
        return layout

    def worker_function(self):
        for i in range(5):
            self.output_queue.put(f"Message from Process: {i}")
            print("test")

    def update_output(self, dt):
        while not self.output_queue.empty():
            message = self.output_queue.get()
            self.output_label.text += f"\n{message}"
            print("test")

if __name__ == '__main__':
    sys.stdout = open('stdout.log', 'w')  # 標準出力をファイルにリダイレクト
    MyApp().run()
