echo WSL1ではlibffiがBinaryの問題を起こす。WSL2で起動必要。
echo Ubuntu 20.04 buildozerのInstallではManufest NG
echo Ubuntu 20.04 buildozerのSourceをGitでDLしBuildしandroid debugするとOK.
echo Ubuntu 22.04 buildozerのInstallでは
echo Ubuntu 22.04 buildozerのSourceをGitでDLしBuildしandroid debugすると権限問題で停止。sudo buildozer ・・・で起動必要

sudo apt update
sudo apt upgrade
sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

curl https://pyenv.run | bash

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"


#pip3 install --user --upgrade Cython

#export PATH=$PATH:~/.local/bin/
#buildozer version

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



read 

cd ~\buildozer\
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
    # Androidの場合はプロジェクトディレクトリに含めたフォントファイルを使用
    font_path = os.path.join(os.path.dirname(__file__), 'DroidSans.ttf')
    LabelBase.register(DEFAULT_FONT, fn_regular=font_path)
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
buildozer android debug clean
sudo buildozer -v android debug 2>&1 | tee buildozer.log

