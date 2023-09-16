import os
import subprocess

def get_file_list(folder_path):
    try:
        files = os.listdir(folder_path)
        return files
    except FileNotFoundError:
        print(f"フォルダ '{folder_path}' が存在しません。")

def select_from_list(options):
    if not options:
        print("選択肢がありません。")
        return None

    print("選択肢:")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

    while True:
        try:
            choice = int(input("選択したい項目の番号を入力してください (0 で終了): "))
            if choice == 0:
                return None
            elif choice < 1 or choice > len(options):
                print("無効な選択です。再試行してください。")
            else:
                return options[choice - 1]
        except ValueError:
            print("無効な入力です。番号を入力してください。")

def execute_selected_file():
    file_path = input("ファイルパスを入力してください: ")
    folder_path = os.path.dirname(file_path)

    files = get_file_list(folder_path)
    selected_file = select_from_list(files)

    if selected_file is not None:
        file_path = os.path.join(folder_path, selected_file)
        subprocess.run(file_path, shell=True)

if __name__ == "__main__":
    execute_selected_file()
