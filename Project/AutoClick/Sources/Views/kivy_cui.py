import multiprocessing
import time
import sys
from kivy_popup import MyApp  # popup_guiのAppを直接インポート
sys.path.append("./Sources/Common")
sys.path.append("./Common")
import SharedMemory
def launch_popup(shared_memory_name, key_name):
    # Kivyのアプリを起動して、結果を共有メモリにxxb保存
    MyApp(shared_memory_name, key_name).run()

def main():
    # 共有メモリを作成
    shared_memory_name = "shared_memory.dat"
    # 保存するKey名と共有メモリ名を設定
    key_name = "user_input"

    # サブプロセスでポップアップを起動し、共有メモリとキー名を渡す
    process = multiprocessing.Process(target=launch_popup, args=(shared_memory_name,key_name))
    
    # サブプロセスを開始
    process.start()

    # サブプロセスの終了を待つ
    process.join()
    # 共有メモリからデータを取得
    shared_dict = SharedMemory.read_from_shared_memory(shared_memory_name)
    user_input = shared_dict.get(key_name, None)
    
    if user_input:
        print(f"User input from shared memory: {user_input}")
    else:
        print("No input received.")

if __name__ == '__main__':
    main()
