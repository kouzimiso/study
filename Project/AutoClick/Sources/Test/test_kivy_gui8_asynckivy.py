from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from asynckivy import sleep
import asynckivy

class PopupForm_sleep(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Input Form"
        
        # レイアウト設定
        layout = BoxLayout(orientation='vertical')
        
        # テキスト入力フィールド
        self.text_input = TextInput(hint_text="Enter some value")
        layout.add_widget(self.text_input)
        
        # OKボタン
        submit_button = Button(text="Submit")
        submit_button.bind(on_press=lambda instance: asynckivy.start(self.on_submit(instance)))  # コルーチンを起動
        layout.add_widget(submit_button)
        
        self.add_widget(layout)
        self.result = None  # 結果を保存する変数

    async def on_submit(self, instance):
        # 結果を取得してポップアップを閉じる
        self.result = self.text_input.text
        self.dismiss()  # ポップアップを閉じる

    async def get_result(self):
        # ポップアップを開く
        self.open()
        
        # ポップアップが閉じられるのを待機する
        while self.result is None:
            await sleep(0.1)  # asynckivyのsleepを使用
        
        return self.result
    
class PopupForm(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Input Form"
        
        # レイアウト設定
        layout = BoxLayout(orientation='vertical')
        
        # テキスト入力フィールド
        self.text_input = TextInput(hint_text="Enter some value")
        layout.add_widget(self.text_input)
        
        # OKボタン
        submit_button = Button(text="Submit")
        submit_button.bind(on_press=self.on_submit)
        layout.add_widget(submit_button)
        
        self.add_widget(layout)
        self.result = None  # 結果を保存する変数
        self.event = asynckivy.Event()  # イベントオブジェクトを作成

    def on_submit(self, instance):
        # 結果を取得してポップアップを閉じる
        self.result = self.text_input.text
        self.dismiss()  # ポップアップを閉じる
        self.event.set()  # イベントを設定（再開のシグナルを送る）

    async def get_result(self):
        # ポップアップを開く
        self.open()

        # ポップアップが閉じられるのをイベントで待機
        await self.event.wait()

        return self.result
    
class TestApp(App):
    async def show_popup(self):
        popup_form = PopupForm()
        result = await popup_form.get_result()
        print(f"Popup result: {result}")
        popup_form = PopupForm_sleep()
        result = await popup_form.get_result()
        print(f"Popup result_sleep: {result}")


    def run_async_popup(self):
        asynckivy.start(self.show_popup())  # asynckivyを使用してコルーチンを開始

    def build(self):
        layout = BoxLayout(orientation='vertical')
        show_popup_button = Button(text="Show Popup")
        show_popup_button.bind(on_press=lambda instance: self.run_async_popup())
        layout.add_widget(show_popup_button)
        return layout
    
if __name__ == "__main__":
    TestApp().run()
