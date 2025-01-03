import subprocess
import os
import platform
import sys

def run_command(directory_path, command):
    """
    指定されたプロジェクトディレクトリでコマンドを実行する。
    
    Args:
        directory_path (str): コマンドを実行するプロジェクトのディレクトリパス。
        command (str): 実行するコマンド。
        
    Returns:
        None
    """
    try:
        # 現在の作業ディレクトリを保存
        original_dir = os.getcwd()
        
        # プロジェクトディレクトリに移動
        os.chdir(directory_path)
        
        # コマンドを実行
        print(f"Running Command in {directory_path} with command: {command}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,  # 標準出力を取得
            stderr=subprocess.STDOUT,  # 標準エラーを標準出力に統合
            universal_newlines=True,  # 出力を文字列として扱う
            shell=True,  # シェルを通してコマンドを実行
        )

        # 実行中の出力をリアルタイム表示
        for line in process.stdout:
            print(line, end="")  # 出力をリアルタイムに表示
        
        # プロセスの終了を待つ
        process.wait()
        
        if process.returncode == 0:
            print("\nコマンドの実行が完了しました！")
        else:
            print(f"\nコマンドの実行が失敗しました。終了コード: {process.returncode}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

    finally:
        # 元の作業ディレクトリに戻る
        os.chdir(original_dir)

if __name__ == "__main__":
    # 引数の取得
    args = sys.argv[1:]
    default_path = "./"
    default_command = "setup_buildozer_mac.sh"
    if len(args) == 2:
        directory_path = args[0]
        command = args[1]
    elif len(args) == 1:
        directory_path = args[0]
        command = default_command
    else:
        # デフォルト設定
        directory_path = default_path
        command = default_command

    # コマンドを実行
    run_command(directory_path, command)