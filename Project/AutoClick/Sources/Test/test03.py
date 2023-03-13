import sys
from kivy.app import App
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class EditorGUI(BoxLayout):
    def __init__(self, data, **kwargs):
        super(EditorGUI, self).__init__(**kwargs)
        self.data = data
        self.padding = 20
        self.orientation = 'vertical'

        # kvファイルで定義されたリストを読み込み、動的にウィジェットを作成
        for key, value in self.data.items():
            self.add_widget(Label(text=key))
            self.add_widget(TextInput(text=value))

        # 更新ボタンを作成
        btn = Button(text='Update')
        btn.bind(on_press=self.update_data)
        self.add_widget(btn)

        # 終了ボタンを作成
        btn = Button(text='Close Window')
        btn.bind(on_press=self.close)
        self.add_widget(btn)

    def update_data(self, obj):
        # 辞書データを更新
        for i in range(0, len(self.children), 2):
            key = self.children[i].text
            value = self.children[i+1].text
            self.data[key] = value

        # コンソールに辞書データを表示
        print(self.data)

    def close(self, obj):
        # コンソールに辞書データを表示して終了
        self.update_data(None)
        App.get_running_app().stop()
        Window.close()


class DictionaryEditor(App):
    def on_stop(self):
        Logger.critical('App: Aaaargh I\'m dying!')

    def build(self):
        Window.borderless = True
        return EditorGUI(data=self.data)

    def on_pause(self):
        # バックグラウンドに回るときに辞書データを更新して返す
        return self.data

    def on_resume(self):
        pass

    def run(self, data):
        self.data = data
        super(DictionaryEditor, self).run()
        return self.data


def main():
    data = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3'
    }
    data = DictionaryEditor().run(data)
    print(data)


if __name__ == "__main__":
    sys.exit(main())
