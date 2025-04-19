import subprocess
import os

wsl_directory = '/home/kouzimiso/study'  # WSL内で作業したいディレクトリ
# WSL内のカレントディレクトリを変更
os.chdir('C:')  # Pythonのカレントディレクトリを変更

# WSL上のシェルスクリプトのパス（WSL内のパス形式に修正）
wsl_script_path = '/home/kouzimiso/study/setup_buildozer.sh'

# 実行権限を付与するためのchmodコマンド
chmod_command = ['wsl', 'chmod', '+x', wsl_script_path]
try:
    subprocess.run(chmod_command, check=True)
    print("Permissions updated successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error updating permissions: {e}")
    print("stdout:", e.stdout)
    print("stderr:", e.stderr)

# WSLコマンドを使ってシェルスクリプトを実行
command = ['wsl', 'bash', '-c', wsl_script_path]  # WSL内のパスで実行
output_lines = []  # 出力全体を保存するリスト
try:
    # subprocess.runでコマンドを実行し、その結果を取得
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,  # 標準出力を取得
        stderr=subprocess.STDOUT,  # 標準エラーを標準出力に統合
        universal_newlines=True,  # 出力を文字列として扱う
        shell=True,  # シェルを通してコマンドを実行
    )

    # 実行中の出力をリアルタイム表示（エンコーディングを指定してデコード）
    for line in process.stdout:
        try:
            print(line, end="")  # 出力をリアルタイムに表示
            output_lines.append(line)  # 出力をリストに保存
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")
            print("Skipping problematic line.")

    # プロセスの終了を待つ
    process.wait()
    output = "".join(output_lines)

except subprocess.CalledProcessError as e:
    print(f"Error executing script: {e}")
    print("stdout:", e.stdout)
    print("stderr:", e.stderr)
except UnicodeDecodeError as e:
    print(f"UnicodeDecodeError: {e}")
    print("output_lines:", output_lines)
