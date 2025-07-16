import os
import subprocess
import sys
import shlex
import datetime
import logging
import Process
# ログ設定
LOG_FILE = "compile_checker.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

class CompilationError(Exception):
    """コンパイルエラーを表すカスタム例外"""
    pass

def get_timestamp() -> str:
    """現在のタイムスタンプを取得"""
    return datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

def get_python_files(folder: str):
    """指定フォルダ内のPythonファイル一覧を取得"""
    try:
        files = [f for f in os.listdir(folder) if f.endswith(".py")]
        if not files:
            logging.warning(f"{folder} に Python ファイルがありません。")
        return files
    except Exception as e:
        logging.error(f"フォルダの取得エラー: {e}")
        return []

def execute_script(script_path: str) -> str:
    """.py スクリプトを実行し、その標準出力を取得"""
    try:
        #result = Process.execute_external_program(sys.executable, script_path)
        result = subprocess.run([sys.executable, script_path], capture_output=True, input="\n",  text=True, shell=True, check=True)
        logging.info(f"実行成功: {script_path}")
        return result
    except Exception as e:
        logging.error(f"スクリプト実行エラー: {script_path} - {e}")
        return f"Execution Error: {str(e)}"

def compile_script(script_path: str) -> bool:
    """PyInstaller でスクリプトをコンパイルし、成功したかどうかを返す"""
    try:
        result = Process.execute_external_program(sys.executable,["-m","PyInstaller", "--onefile" ,script_path])
        logging.info(f"コンパイル成功: {script_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"コンパイル失敗: {script_path} - {e}")
        raise CompilationError(f"コンパイル失敗: {script_path}") from e

def get_compiled_exe_path(script_path: str) -> str:
    """コンパイルされた .exe のパスを取得"""
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    return os.path.join("dist", f"{script_name}.exe")

def execute_exe(exe_path: str) -> str:
    """コンパイル済み .exe を実行し、その標準出力を取得"""
    try:
        result = subprocess.run(exe_path, capture_output=True, input="\n",  text=True, shell=True, check=True)
        logging.info(f"実行成功: {exe_path}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f".exe 実行エラー: {exe_path} - {e}")
        return f"Execution Error: {str(e)}"

def main(folder: str):
    """メイン処理"""
    if not os.path.exists(folder):
        logging.error(f"指定されたフォルダが見つかりません: {folder}")
        return

    py_files = get_python_files(folder)
    if not py_files:
        logging.warning("コンパイル対象の .py ファイルが見つかりません。")
        return

    results = []

    for py_file in py_files:
        py_path = os.path.join(folder, py_file)
        exe_path = get_compiled_exe_path(py_path)

        logging.info(f"Compiling: {py_file} ...")
        try:
            compile_success = compile_script(py_path)
        except CompilationError:
            compile_success = False

        # 実行結果の取得
        py_output = execute_script(py_path)
        exe_output = execute_exe(exe_path) if compile_success else "N/A"
        same_output = py_output == exe_output if compile_success else "N/A"
        message=f"{get_timestamp()} | File: {py_file} | Compiled: {compile_success} | Same Output: {same_output}"
        logging.info(message)
        # 結果をリストに保存
        results.append(message)

    # 結果をファイルに出力
    result_file = os.path.join(folder, "compile_results.txt")
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        logging.info(f"結果を {result_file} に保存しました。")
    except Exception as e:
        logging.error(f"結果ファイルの保存エラー: {e}")

if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    main(folder_path)
