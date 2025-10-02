import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty

kivy.require("2.0.0")


class ConfirmPopup(Popup):
    """Observerパターン的な確認ポップアップ"""
    result = BooleanProperty(None)  # Yes=True, No=False を格納

    def __init__(self, title, text, **kwargs):
        super().__init__(title=title, size_hint=(0.7, 0.3), **kwargs)

        box = BoxLayout(orientation='vertical', spacing=10, padding=10)
        box.add_widget(Label(text=text, size_hint_y=None, height='40dp'))

        btn_layout = BoxLayout(spacing=10, size_hint_y=None, height='40dp')
        yes_btn = Button(text='Yes')
        no_btn = Button(text='No')

        yes_btn.bind(on_release=lambda *a: self._set_result(True))
        no_btn.bind(on_release=lambda *a: self._set_result(False))

        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        box.add_widget(btn_layout)

        self.content = box

    def _set_result(self, value):
        """内部でresultを更新 → バインド先に通知"""
        self.result = value
        self.dismiss()


class TestGUI(BoxLayout):
    """メインのGUIレイアウト"""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        # テスト用UI
        self.add_widget(Label(text="sample for delete item popup",
                              size_hint_y=None, height="40dp"))
        btn = Button(text="Delete item")
        btn.bind(on_release=lambda *a: self.confirm_delete_item("dummy_path", "sample_key"))
        self.add_widget(btn)

    def get_current_data(self, path):
        """ダミーのデータ取得"""
        return {"sample_key": "value"}

    def confirm_delete_item(self, path, key):
        """削除確認ポップアップを開く"""
        current_data = self.get_current_data(path)
        is_list = isinstance(current_data, list)

        key_str = f"'{key}'" if not is_list else f"Index {key}"
        title = "Confirm Deletion"
        text = f"Delete {key_str}?"

        popup = ConfirmPopup(title, text)
        popup.bind(result=lambda instance, value: self.handle_delete_confirmation(value, path, key))
        popup.open()

    def handle_delete_confirmation(self, confirm, path, key):
        """削除確認ポップアップからの応答を処理"""
        if confirm:
            self.on_delete_item(path, key)
        else:
            print("Canceled")

    def on_delete_item(self, path, key):
        """実際の削除処理"""
        print(f"Delete: path={path}, key={key}")


class ConfirmDeleteApp(App):
    def build(self):
        return TestGUI()


if __name__ == "__main__":
    ConfirmDeleteApp().run()
