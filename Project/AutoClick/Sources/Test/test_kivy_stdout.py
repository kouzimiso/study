import sys
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class OutputLabel(Label):
    def __init__(self, **kwargs):
        super(OutputLabel, self).__init__(**kwargs)
        self.text = ''  # テキストを初期化

    def write(self, text):
        self.text += text  # テキストを追加

class MyApp(App):
    def build(self):
        self.output_label = OutputLabel()
        sys.stdout = self.output_label  # 標準出力をOutputLabelにリダイレクト
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.output_label)
        print("test")
        print("test")
        print("test")
        return layout

if __name__ == '__main__':
    MyApp().run()
