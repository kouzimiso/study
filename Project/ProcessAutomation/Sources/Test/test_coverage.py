# test_coverage.py

import subprocess
import webbrowser
import os
import sys

def run_coverage(test_file_path: str = "Sources/Test/test_math_utils.py"):
    try:
        # 1. coverage 実行（coverage コマンドを Python 経由で呼び出し）
        subprocess.run([sys.executable, "-m", "coverage", "run", "-m", "pytest", test_file_path], check=True)

        # 2. HTMLレポート生成
        subprocess.run([sys.executable, "-m", "coverage", "html"], check=True)

        # 3. HTMLファイルをブラウザで開く
        report_path = os.path.abspath("htmlcov/index.html")
        webbrowser.open(f"file://{report_path}")
        print(f"✅ カバレッジレポートを開きました: {report_path}")

    except subprocess.CalledProcessError as e:
        print("❌ エラーが発生しました:", e)
        sys.exit(1)

if __name__ == "__main__":
    # 任意のファイルを引数で渡せるように
    test_file = sys.argv[1] if len(sys.argv) > 1 else "Sources/Test/test_math_utils.py"
    run_coverage(test_file)