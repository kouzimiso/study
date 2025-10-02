import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

kivy.require("2.0.0")


def show_confirm_popup(title, text, callback, **kwargs):
    """シンプルな確認ポップアップを表示する"""
    box = BoxLayout(orientation='vertical', spacing=10, padding=10)
    box.add_widget(Label(text=text, size_hint_y=None, height='40dp'))

    # Yes / No ボタン配置
    btn_layout = BoxLayout(spacing=10, size_hint_y=None, height='40dp')
    yes_btn = Button(text='Yes')
    no_btn = Button(text='No')

    popup = Popup(title=title, content=box, size_hint=(0.7, 0.3), **kwargs)

    # ボタン押下時の動作
    yes_btn.bind(on_release=lambda *args: (popup.dismiss(), callback(True)))
    no_btn.bind(on_release=lambda *args: (popup.dismiss(), callback(False)))

    btn_layout.add_widget(yes_btn)
    btn_layout.add_widget(no_btn)
    box.add_widget(btn_layout)
    popup.open()


class TestGUI(BoxLayout):
    """メインのGUIレイアウト"""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        # テスト用ボタン
        self.add_widget(Label(text="sample for delete item popup", size_hint_y=None, height="40dp"))
        btn = Button(text="Delete item")
        btn.bind(on_release=lambda *args: self.confirm_delete_item("dummy_path", "sample_key"))
        self.add_widget(btn)

    def get_current_data(self, path):
        """ダミーのデータ取得（実際のアプリではデータソースに置き換える）"""
        return {"sample_key": "value"}

    def confirm_delete_item(self, path, key):
        """要素の削除を実行前にユーザーに確認する"""
        current_data = self.get_current_data(path)
        is_list = isinstance(current_data, list)

        key_str = f"'{key}'" if not is_list else f"Index {key}"
        title = "Confirm Deletion"
        text = f"Delete {key_str}?"

        show_confirm_popup(title, text, lambda confirm: self.handle_delete_confirmation(confirm, path, key))

    def handle_delete_confirmation(self, confirm, path, key):
        """削除確認ポップアップからの応答を処理"""
        if confirm:
            self.on_delete_item(path, key)
        else:
            print("Canceled")

    def on_delete_item(self, path, key):
        """実際の削除処理（ここではprintで代替）"""
        print(f"Delete: path={path}, key={key}")


class ConfirmDeleteApp(App):
    def build(self):
        return TestGUI()


if __name__ == "__main__":
    ConfirmDeleteApp().run()
