#!/bin/bash

# 更新とアップグレード
echo "Updating and upgrading the system..."
sudo apt update
sudo apt upgrade -y

# 必要なパッケージのインストール
echo "Installing required packages..."
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git openjdk-17-jdk unzip autoconf
# pyenvをインストール
echo "Installing pyenv..."
curl https://pyenv.run | bash

# 環境変数の設定
sudo export PYENV_ROOT="$HOME/.pyenv"
sudo export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

# .bashrc または .zshrc に pyenv の設定を追加
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# 設定を反映
source ~/.bashrc

# pyenvを使用してPython 3.11をインストール
echo "Installing Python 3.11 via pyenv..."
pyenv install 3.11
pyenv global 3.11
pyenv rehash

# 必要なパッケージのインストール
echo "Installing Python packages..."
sudo apt install -y python3-pip

# BuildozerとKivyのインストール
sudo pip install --upgrade pip
sudo pip install kivy cython buildozer

# PATHに~/.local/binを追加
sudo export PATH="$HOME/.local/bin:$PATH"
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
sudo env "PATH=＄HOME/.pyenv/shims:$PATH" buildozer -v android debug 2>&1 | tee buildozer.log
