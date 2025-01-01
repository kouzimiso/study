from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
import re

class SyntaxHighlightTextInput(TextInput):
    # キーワードと色のリスト
    keywords = ListProperty([
        ('def', [1, 0, 0, 1]),       # 赤
        ('class', [0, 0, 1, 1]),     # 青
        ('import', [0, 1, 0, 1]),    # 緑
        ('print', [1, 0.5, 0, 1]),   # オレンジ
    ])

    def __init__(self, **kwargs):
        # highlight_in_progress 属性を初期化
        self.highlight_in_progress = False
        super(SyntaxHighlightTextInput, self).__init__(**kwargs)
        # highlight_in_progress 属性を初期化
        self.highlight_in_progress = False
        # テキストが変更されたときに on_text メソッドを呼び出す
        self.bind(text=self.on_text)

    def on_text(self, instance, value):
        # ハイライト処理中でない場合のみハイライトを実行
        if not self.highlight_in_progress:
            self.highlight_text()

    def highlight_text(self):
        # ハイライト処理中であることを示すフラグを設定
        self.highlight_in_progress = True
        
        text = self.text
        highlighted_text = ''
        last_pos = 0

        # キーワードごとにテキストをハイライト
        for keyword, color in self.keywords:
            pattern = r'\b{}\b'.format(keyword)
            for match in re.finditer(pattern, text):
                start, end = match.span()

                # マッチ前のテキスト
                highlighted_text += text[last_pos:start]
                # マッチしたキーワードに色を適用
                highlighted_text += '[color={}{}{}{}]{}[/color]'.format(*color, keyword)
                last_pos = end

        # 残りのテキストを追加
        highlighted_text += text[last_pos:]

        # ハイライトされたテキストを設定
        self.text = highlighted_text

        # ハイライト処理が完了したのでフラグを解除
        self.highlight_in_progress = False

    def insert_text(self, substring, from_undo=False):
        # テキストを挿入してハイライトを適用
        super(SyntaxHighlightTextInput, self).insert_text(substring, from_undo)
        self.highlight_text()

class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.text_input = SyntaxHighlightTextInput(
            text='def example():\n    print("Hello World")\n    class MyClass:\n        pass\n',
            font_name='RobotoMono-Regular.ttf',
            font_size=16,
        )
        layout.add_widget(self.text_input)
        return layout

if __name__ == '__main__':
    TestApp().run()
