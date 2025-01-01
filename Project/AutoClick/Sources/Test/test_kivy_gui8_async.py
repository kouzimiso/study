
import asyncio
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

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

    def on_submit(self, instance):
        # 結果を取得してポップアップを閉じる
        self.result = self.text_input.text
        self.dismiss()  # ポップアップを閉じる

    async def get_result(self):
        # ポップアップを開く
        self.open()
        
        # ポップアップが閉じられるのを待機する
        while self.result is None:
            await asyncio.sleep(0.1)
        
        return self.result

class TestApp(App):
    async def show_popup(self):
        # PopupFormを作成
        popup_form = PopupForm()
        
        # ポップアップからの結果を取得
        result = await popup_form.get_result()
        print(f"Popup result: {result}")
        
    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        # ボタンを追加してポップアップを表示
        show_popup_button = Button(text="Show Popup")
        show_popup_button.bind(on_press=lambda instance: self.run_async_popup())
        layout.add_widget(show_popup_button)
        
        return layout

    def run_async_popup(self):
        # asyncioのタスクを実行
        Clock.schedule_once(lambda dt: asyncio.create_task(self.show_popup()), 0)

# asyncioを利用してKivyアプリを実行
async def async_run():
    app = TestApp()
    await app.async_run(async_lib='asyncio')

if __name__ == "__main__":
    asyncio.run(async_run())