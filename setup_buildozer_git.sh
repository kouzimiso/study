#!/bin/bash
echo WSL1ではlibffiがBinaryの問題を起こす。WSL2で起動必要。
echo pyenvでのInstallを行うと仮想環境に.buildozerをInstallする為、NGになる事あり。
echo 日本語フォントを使用するとapk起動しない問題あり。ubuntuのフォントを移植する方法が使える。
echo Ubuntu 20.04 buildozerのInstallをし、android debugするとOK.
echo Ubuntu 20.04 buildozerのSourceをGitでDLしBuildしandroid debugするとOK.
echo Ubuntu 22.04 sudoを付けてbuildozer android debugをしないと権限問題で停止。

# システムの更新
echo "Updating and upgrading the system..."
sudo apt update
sudo apt upgrade -y

# 必要なパッケージのインストール
echo "Installing required packages..."
sudo apt-get install -y build-essential wget git zip unzip openjdk-17-jdk  autoconf libtool cmake python3.11 python3-pip fonts-takao
curl https://pyenv.run | bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"


#pip3 install --user --upgrade Cython

#export PATH=$PATH:~/.local/bin/
#buildozer version
# 設定を反映
source ~/.bashrc

pyenv install 3.11

sudo apt install -y python3
pip3 install kivy

cd ~
git clone https://github.com/kivy/buildozer
git pull
cd buildozer
python3 setup.py build
sudo python3 setup.py install


cd ~\buildozer\.buildozer/android/platform/python-for-android
git pull
python3 setup.py build
sudo python3 setup.py install

cd ~\buildozer\.buildozer\android\platform\build-arm64-v8a_armeabi-v7a\build\other_builds\pyjnius-sdl2\armeabi-v7a__ndk_target_21\pyjnius
git pull
python3 setup.py build
sudo python3 setup.py install




cd ~\buildozer\
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

export PATH=$PATH:~/buildozer
buildozer init
# buildozer.specファイルの修正
echo "Updating buildozer.spec file..."
sed -i 's/^source.include_exts = .*/source.include_exts = py,png,jpg,kv,atlas,ttf/' buildozer.spec
sed -i '/^source.include_patterns = /d' buildozer.spec
echo 'source.include_patterns = assets/*.ttf' >> buildozer.spec


buildozer android clean
sudo buildozer -v android debug 2>&1 | tee buildozer.log
