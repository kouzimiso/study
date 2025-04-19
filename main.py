from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.utils import platform
import os

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        button = Button(text='クリックしてください')
        button.bind(on_press=self.on_button_click)
        self.label = Label(text='ボタンがクリックされるとここに表示されます')
        layout.add_widget(button)
        layout.add_widget(self.label)
        return layout

    def on_button_click(self, instance):
        self.label.text = 'ボタンがクリックされました！'

    def set_custom_font(self):
        # フォントファイルのパスを設定
        if platform == 'macosx':
            # macOSの場合はシステムフォントを使用
            font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
        elif platform == 'win':
            # Windowsの場合はシステムフォントを使用
            font_path = "C:/Windows/Fonts/YuGothR.ttc"
        elif platform == 'android':
            # Androidの場合はassetsフォルダ内のフォントを使用
            # assetsフォルダ内のフォントファイルを動的に探す
            assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
            font_files = [f for f in os.listdir(assets_dir) if f.endswith('.ttf') or f.endswith('.ttc')]
            
            if font_files:
                font_path = os.path.join(assets_dir, font_files[0])
                LabelBase.register(DEFAULT_FONT, fn_regular=font_path)
        else:
            # その他のプラットフォームではデフォルトフォントを使用
            font_path = None
        # フォントを登録
        if font_path and os.path.exists(font_path):
            LabelBase.register(DEFAULT_FONT, fn_regular=font_path)

if __name__ == '__main__':
    app = MyApp()
    app.set_custom_font()
    app.run()
