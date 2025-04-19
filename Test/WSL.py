import subprocess
import os
import locale
# WSL内のカレントディレクトリのフルパスを表示
def get_current_directory():
    command = ['wsl', 'pwd']
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        current_directory = result.stdout.strip()
        print(f"Current WSL directory: {current_directory}")

        # Dドライブかローカルホストかを判別
        if '/mnt/d/' in current_directory:
            print("This is running on the D drive in WSL.")
        else:
            print("This is running on the local WSL file system.")

    except subprocess.CalledProcessError as e:
        print(f"Error getting current directory: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)

# 実行権限を付与するためのchmodコマンド
chmod_command = ['wsl', 'chmod', '+x', 'study/setup_buildozer.sh']
try:
    subprocess.run(chmod_command, check=True)
    print("Permissions updated successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error updating permissions: {e}")
    print("stdout:", e.stdout)
    print("stderr:", e.stderr)
    

# カレントディレクトリを確認
get_current_directory()
# WSL パスに変換
wsl_home = subprocess.run(['wsl', 'pwd'], capture_output=True, text=True).stdout.strip()
wsl_script_path = f"{wsl_home}/study/setup_buildozer.sh"

# 実行権限を付与するためのchmodコマンド
chmod_command = ['wsl', 'chmod', '+x', wsl_script_path]
# ... (既存のコード)

# WSLコマンドを使ってシェルスクリプトを実行
command = ['wsl', 'bash', '-c', wsl_script_path]
try:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=False,
    )

    output = b""
    while True:
        line = process.stdout.readline()
        if not line:
            break
        output += line
        try:
            # システムのロケール設定に基づいたエンコーディングでデコード
            encoding = locale.getpreferredencoding()
            encoding ='utf-8'
            decoded_line = line.decode(encoding)
            print(decoded_line, end="")
        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError: {e}")
            print(f"Tried encoding: {encoding}")
            print(f"Raw bytes: {line!r}")
            # 他のエンコーディングを試す（例：UTF-8, Shift-JIS）
            for encoding in ['utf-8', 'shift-jis']:
                try:
                    decoded_line = line.decode(encoding)
                    print(f"Decoded using {encoding}: {decoded_line}")
                    break
                except UnicodeDecodeError:
                    pass
    print("break")
    process.wait()

except subprocess.CalledProcessError as e:
    print(f"Error executing script: {e}")
    print("stdout:", e.stdout.decode('utf-8'))
except UnicodeDecodeError as e:
    print(f"UnicodeDecodeError: {e}")
    print("output:", output)
except Exception as e:
    print(f"Unexpected error: {e}")