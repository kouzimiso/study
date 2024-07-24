#!/bin/bash

# システムの更新
echo "Updating and upgrading the system..."
sudo apt update
sudo apt upgrade -y

# 必要なパッケージのインストール
echo "Installing required packages..."
sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git zip unzip openjdk-17-jdk python3-pip autoconf libtool cmake python3.11

# Pythonのバージョン確認
python3.11 --version

# 必要なPythonパッケージのインストール
echo "Installing Python packages..."
python3.11 -m pip install --upgrade pip
python3.11 -m pip install kivy cython buildozer

# PATHに~/.local/binを追加
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# 設定を反映
source ~/.bashrc

# Buildozerバージョン確認
buildozer version

# サンプルアプリの作成
echo "Creating a sample Kivy app..."
cat << EOF > main.py
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
EOF

# Buildozerプロジェクトの初期化とビルド
echo "Initializing and building the Buildozer project..."
buildozer init
sudo buildozer -v android debug 2>&1 | tee buildozer.log
