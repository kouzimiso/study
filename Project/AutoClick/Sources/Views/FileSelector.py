import os

def list_files_and_folders(path):
    """
    指定されたパスの子ファイルと子フォルダを表示する関数。
    フォルダは一行ずつ表示し、ファイルはカンマ区切りで表示する。
    """
    print(f"Current Directory: {path}")
    items = os.listdir(path)
    folders = []
    files = []
    
    for item in items:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            folders.append(f"Directory: {item}")
        elif os.path.isfile(item_path):
            files.append(item)
    
    for folder in folders:
        print(folder)
    
    if files:
        print(", ".join(files))

def get_file_path_by_name(path, file_name):
    """
    指定されたディレクトリ内でファイル名に一致するファイルの絶対パスを取得する関数。
    """
    for root, _, files in os.walk(path):
        if file_name in files:
            return os.path.abspath(os.path.join(root, file_name))
    return None

def select_file_or_folder_path(current_path):
    show_list = True
    while True:
        if show_list:
            list_files_and_folders(current_path)
        show_list = True        
        user_input = input("Enter folder or file name (. to quit): ")
        
        if user_input == ".":
            print(f"Current Path: {current_path}")
            return current_path
        
        file_path = get_file_path_by_name(current_path, user_input)
        if file_path:
            print(f"File Path: {file_path}")
            return file_path
            
        else:
            user_input_path = os.path.join(current_path, user_input)
            
            if os.path.exists(user_input_path):
                if os.path.isdir(user_input_path):
                    current_path = user_input_path
                else:
                    print("Not a valid file or folder.")
            else:
                print("File or folder does not exist.")
                show_list = False  # 不正なパスが入力された場合、再表示をスキップ

def main():
    current_path = os.getcwd()
    selected_path = select_file_or_folder_path(current_path)

if __name__ == "__main__":
    main()
