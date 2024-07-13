#!/bin/bash

# 更新とアップグレード
echo "Updating and upgrading the system..."
sudo apt update
sudo apt upgrade -y

# 必要なパッケージをインストール
echo "Installing necessary packages..."
sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git

# pyenvをインストール
echo "Installing pyenv..."
curl https://pyenv.run | bash

# 環境変数の設定
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

# PATHを追加
export PATH=$PATH:~/.local/bin/

# BuildozerとKivyのインストール
echo "Installing Kivy and Buildozer..."
pip3 install kivy
pip3 install --user --upgrade buildozer

# 追加の必要なパッケージをインストール
echo "Installing additional packages..."
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Cythonのインストール
echo "Installing Cython..."
pip3 install --user --upgrade Cython

# Buildozerバージョン確認
buildozer version

# Python + Kivyプログラムの作成
echo "Creating a sample Kivy program..."
mkdir -p ~/Buildozer
cd ~/Buildozer

cat << EOF > main.py
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

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

# pyenvを使用してPython 3.11をインストール
echo "Installing Python 3.11 via pyenv..."
pyenv install 3.11

# 必要に応じてpyenvの再設定
if [ $? -ne 0 ]; then
    echo "Reconfiguring pyenv..."
    sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv virtualenv-init -)"
    exec "$SHELL"
fi

# Buildozerプロジェクトの初期化とビルド
echo "Initializing and building the Buildozer project..."
buildozer init

# ビルドの前にシェルの再読み込み
exec "$SHELL"

# Buildozerのビルド
buildozer -v android debug

# Buildozerの最新開発版のインストール手順
if [ $? -ne 0 ]; then
    read -p "Buildozerのビルドに失敗しました。最新開発版をインストールして再試行しますか？ (y/n): " user_input
    if [ "$user_input" = "y" ] || [ "$user_input" = "Y" ]; then
        echo "Downloading and installing the latest development version of Buildozer..."
        pip uninstall -y buildozer
        git clone https://github.com/kivy/buildozer.git
        cd buildozer
        git pull
        python3 setup.py build
        sudo python3 setup.py install
        export PATH=$PATH:~/buildozer
        cd ..
        buildozer -v android debug
    else
        echo "Buildozerの最新開発版のインストールをキャンセルしました。"
    fi
fi
