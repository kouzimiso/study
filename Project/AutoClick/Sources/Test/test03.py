import sys
import keyboard

# アイテムのリストを定義する
items = ["apple", "banana", "orange", "grape", "kiwi"]
selected_item = 0

# 検索文字列でフィルタリングする
def filter_items(search_string):
    filtered_items = []
    for item in items:
        if search_string.lower() in item.lower():
            filtered_items.append(item)
    return filtered_items
    # return [item for item in items if search_string.lower() in item.lower()]

# 検索結果の中で選択されたアイテムのインデックスを返す
def get_selected_item_index(search_string=None):
    #filtered_items = filter_items(search_string) if search_string else items
    #return min(len(filtered_items) - 1, max(0, selected_item))
    if search_string:
        filtered_items = filter_items(search_string)
    else:
        filtered_items = items
    return min(len(filtered_items) - 1, max(0, selected_item))
# プロンプトと検索ボックスを表示する
def show_prompt(search_string=None):
   # filtered_items = filter_items(search_string) if search_string else items
    if search_string:
        filtered_items = filter_items(search_string)
    else:
        filtered_items = items
    print("Select an item:")
    for i, item in enumerate(filtered_items):
        if i == selected_item:
            print("> " + item)
        else:
            print("  " + item)
    print("")
    if search_string:
        print("Search: " + search_string)
    else:
        print("Search: ")

# ユーザー入力を処理する
def handle_input(search_string=None):
    global selected_item
    show_prompt(search_string)
    while True:
        key = keyboard.read_event().name
        if key == "up":
            selected_item = max(0, selected_item - 1)
            show_prompt(search_string)
        elif key == "down":
            filtered_items = filter_items(search_string)
            selected_item = min(len(filtered_items) - 1, selected_item + 1)
            show_prompt(search_string)
        elif key == "esc":
            sys.exit()
        elif key.startswith("search "):
            search_string = key[7:]
            selected_item = 0
            show_prompt(search_string)
        elif key == "enter":
            break
    if len(search_string) > 0:
        handle_input(search_string)
    else:
        handle_input()

# プログラムを開始する
handle_input()
