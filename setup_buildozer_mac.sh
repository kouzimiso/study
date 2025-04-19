#!/bin/bash

echo "macOSでのBuildozerとKivyの設定を開始します。"

# 必要なコマンドラインツールのインストール
echo "Xcode Command Line Toolsのインストールを確認..."
xcode-select --install

# Homebrewのインストール確認
if ! command -v brew &> /dev/null; then
    echo "Homebrewが見つかりません。Homebrewをインストールします。"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrewは既にインストールされています。"
fi

# 必要なパッケージのインストール
echo "必要なパッケージをインストールします..."
brew install git wget python@3.11 openjdk

# Pythonのバージョン確認
echo "Pythonのバージョン確認..."
python3.11 --version

# pyenvのインストールと設定
if ! command -v pyenv &> /dev/null; then
    echo "pyenvが見つかりません。pyenvをインストールします。"
    brew install pyenv
fi

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
echo 'eval "$(pyenv init --path)"' >> ~/.bash_profile
source ~/.bash_profile

# Python 3.11のインストールと設定
echo "Python 3.11のインストールと設定..."
pyenv install 3.11.4
pyenv global 3.11.4

# 仮想環境の作成とアクティベート
echo "仮想環境を作成し、アクティベートします..."
python3 -m venv kivy_env
source kivy_env/bin/activate

# 必要なPythonパッケージのインストール
echo "必要なPythonパッケージをインストールします..."
pip install --upgrade pip
pip install setuptools
pip install kivy cython buildozer

# 日本語フォントのコピー元をビルド環境に応じて設定
echo "日本語フォントをassetsフォルダにコピーします..."
mkdir -p assets

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOSの場合
    cp "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc" assets/
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linuxの場合
    cp /usr/share/fonts/truetype/fonts-japanese-gothic.ttf assets/
fi
#echo Press Enter to continue...
#read
# Buildozerバージョン確認
echo "Buildozerのバージョン確認..."
buildozer --version

# サンプルアプリの作成
echo "サンプルKivyアプリを作成します..."
cat << EOF > main.py
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
EOF

# Buildozerプロジェクトの初期化
echo "Buildozerプロジェクトを初期化します..."
buildozer init

# buildozer.specファイルの修正
echo "buildozer.specファイルを更新します..."
sed -i '' 's/^source.include_exts = .*/source.include_exts = py,png,jpg,kv,atlas,ttf,ttc/' buildozer.spec
sed -i '' '/^source.include_patterns = /d' buildozer.spec
echo 'source.include_patterns = assets/*.ttf, assets/*.ttc' >> buildozer.spec

# ビルド
echo "ビルドを開始します..."
buildozer android clean
buildozer -v android debug 2>&1 | tee buildozer.log
