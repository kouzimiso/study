import psutil

def list_processes():
    # すべての実行中のプロセスを取得
    processes = list(psutil.process_iter(attrs=['pid', 'name']))
    
    print("プロセス一覧:")
    for idx, process in enumerate(processes, start=1):
        process_info = process.info()
        print(f"{idx}. PID: {process_info['pid']} - Name: {process_info['name']}")
    
    return processes

def close_process(process):
    try:
        process.terminate()
        print(f"プロセス {process.info()['name']} (PID: {process.info()['pid']}) を終了しました。")
    except psutil.NoSuchProcess:
        print("プロセスが見つかりません。")
    except psutil.AccessDenied:
        print("アクセスが拒否されました。")

if __name__ == "__main__":
    # プロセス一覧を表示
    processes = list_processes()
    
    if len(processes) == 0:
        print("実行中のプロセスがありません。")
    else:
        # ユーザーにプロセスの選択を求める
        while True:
            try:
                choice = int(input("終了させるプロセスの番号を選択してください (0 で終了): "))
                
                if choice == 0:
                    break
                
                if 1 <= choice <= len(processes):
                    selected_process = processes[choice - 1]
                    close_process(selected_process)
                else:
                    print("無効な選択です。正しい番号を選んでください。")
            except ValueError:
                print("無効な入力です。数値を入力してください。")
