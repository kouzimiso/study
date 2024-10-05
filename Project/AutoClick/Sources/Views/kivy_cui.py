import subprocess
import multiprocessing
import time
import os

def main():
    # 共有メモリを作成
    manager = multiprocessing.Manager()
    shared_dict = manager.dict()

    # 保存するKey名と共有メモリ名を設定
    key_name = "user_input"

    # サブプロセスでポップアップを起動し、共有メモリとキー名を渡す
    process = subprocess.Popen(['python', 'Sources/Views/kivy_popup.py', key_name],
                               env={**os.environ, 'SHARED_DICT_ID': str(shared_dict._id)})

    # サブプロセスの終了を待つ
    process.wait()

    # 共有メモリからデータを取得
    user_input = shared_dict.get(key_name, None)
    
    if user_input:
        print(f"User input from shared memory: {user_input}")
    else:
        print("No input received.")

if __name__ == '__main__':
    main()