dir_path="./buildozer"
if [ ! -d "$dir_path" ]; then
    git clone https://github.com/kivy/buildozer
fi
cd buildozer
python3 setup.py build
pip install -e .

`which buildozer`
# if there is no result, and you installed with --user, add this line at the end of your `~/.bashrc` file.
export PATH=~/.local/bin/:$PATH
# and then run
. ~/.bashrc
cd ..
buildozer init
buildozer android debug deploy run > build_output.log 2>&1