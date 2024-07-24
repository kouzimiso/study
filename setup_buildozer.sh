#!/bin/bash
echo WSL1ではlibffiがBinaryの問題を起こす。WSL2で起動必要。
echo pyenvでのInstallを行うと仮想環境に.buildozerをInstallする為、NGになる事あり。
echo 日本語フォントを使用するとapk起動しない問題あり。ubuntuのフォントを移植する方法が使える。
echo Ubuntu 20.04 buildozerのInstallをし、android debugするとOK.
echo Ubuntu 20.04 buildozerのSourceをGitでDLしBuildしandroid debugするとOK.
echo Ubuntu 22.04 sudoを付けてbuildozer android debugをしないと権限問題で停止。

# システムの更新
# システムの更新
echo "Updating and upgrading the system..."
sudo apt update
sudo apt upgrade -y

# 必要なパッケージのインストール
echo "Installing required packages..."
sudo apt-get install -y build-essential wget git zip unzip openjdk-17-jdk  autoconf libtool cmake python3.11 python3-pip

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

# 日本語フォントをassetsフォルダにコピー
echo "Copying Japanese font to assets folder..."
mkdir -p assets
cp /usr/share/fonts/truetype/fonts-japanese-gothic.ttf assets/

# Buildozerバージョン確認
buildozer version
read 

# サンプルアプリの作成
echo "Creating a sample Kivy app..."
cat << EOF > main.py
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.utils import platform

# フォントのパスを指定してフォントを設定する
if platform == 'win':
    # Windowsの場合はシステムフォントを使用
    font_path = "C:/Windows/Fonts/YuGothR.ttc"
    LabelBase.register(DEFAULT_FONT, fn_regular=font_path)
elif platform == 'android':
    # Androidの場合はassetsフォルダ内のフォントを使用
    LabelBase.register(DEFAULT_FONT, fn_regular='assets/fonts-japanese-gothic.ttf')
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
# buildozer.specファイルの修正
echo "Updating buildozer.spec file..."
sed -i 's/^source.include_exts = .*/source.include_exts = py,png,jpg,kv,atlas,ttf/' buildozer.spec
sed -i '/^source.include_patterns = /d' buildozer.spec
echo 'source.include_patterns = assets/*.ttf' >> buildozer.spec


buildozer android clean
sudo buildozer -v android debug 2>&1 | tee buildozer.log
