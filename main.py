from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from kivy.lang import Builder
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.utils import platform
# システムフォントのパスを指定してフォントを設定する
font_path = "C:/Windows/Fonts/YuGothR.ttc"

if platform == 'win':
    # Windowsの場合はシステムフォントを使用
    LabelBase.register(DEFAULT_FONT, fn_regular=font_path)
elif platform == 'android':
    # Androidの場合は適切なフォントを指定する
    LabelBase.register(DEFAULT_FONT, fn_regular='DroidSans.ttf')
else:
    # その他のプラットフォームではデフォルトフォントを使用
    LabelBase.register(DEFAULT_FONT, fn_regular='DejaVuSans.ttf')


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

if __name__ == '__main__':
    MyApp().run()
