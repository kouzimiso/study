import os
import sys
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import multiprocessing

class InputPopup(Popup):
    def __init__(self, key_name, shared_dict, **kwargs):
        super(InputPopup, self).__init__(**kwargs)
        self.shared_dict = shared_dict
        self.key_name = key_name

        # レイアウトの作成
        self.layout = BoxLayout(orientation='vertical')
        self.text_input = TextInput(hint_text='Enter your input here', multiline=False)
        self.submit_button = Button(text='Submit', on_press=self.submit)

        self.layout.add_widget(self.text_input)
        self.layout.add_widget(self.submit_button)
        
        # レイアウトをPopupのcontentとして設定
        self.content = self.layout

    def submit(self, instance):
        # ユーザーの入力を共有メモリに保存
        self.shared_dict[self.key_name] = self.text_input.text
        self.dismiss()  # ポップアップを閉じる

class MyApp(App):
    def __init__(self, key_name, shared_dict, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.key_name = key_name
        self.shared_dict = shared_dict

    def build(self):
        # ポップアップを表示
        popup = InputPopup(self.key_name, self.shared_dict)
        popup.open()  # ポップアップを開く

        # buildメソッドはウィジェットを返す必要がない
        return BoxLayout()  # 空のウィジェットを返す

if __name__ == '__main__':
    # コマンドライン引数を取得
    key_name = sys.argv[1] if len(sys.argv) > 1 else 'user_input'
    
    # 共有メモリIDを取得
    shared_dict_id = os.environ.get('SHARED_DICT_ID')
    
    # 共有メモリを初期化
    manager = multiprocessing.Manager()
    shared_dict = manager.dict()
    
    # アプリを起動
    MyApp(key_name, shared_dict).run()