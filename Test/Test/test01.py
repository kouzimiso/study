import sys

# アイテムのリストを定義する
items = ["apple", "banana", "orange", "grape", "kiwi"]
selected_item = 0

# 検索文字列でフィルタリングする
def filter_items(search_string):
    return [item for item in items if search_string.lower() in item.lower()]

# 検索結果の中で選択されたアイテムのインデックスを返す
def get_selected_item_index(search_string=None):
    filtered_items = filter_items(search_string) if search_string else items
    return min(len(filtered_items) - 1, max(0, selected_item))

# プロンプトと検索ボックスを表示する
def show_prompt(search_string=None):
    filtered_items = filter_items(search_string) if search_string else items
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
    user_input = input("> ")
    if user_input == "up":
        selected_item = max(0, selected_item - 1)
    elif user_input == "down":
        selected_item = min(len(filter_items(search_string)) - 1, selected_item + 1)
    elif user_input.startswith("search "):
        search_string = user_input[7:]
        selected_item = 0
    elif user_input == "quit":
        sys.exit()
    elif len(user_input) > 0:
        search_string = user_input
        selected_item = 0
    else:
        selected_item = get_selected_item_index(search_string)
    handle_input(search_string)

# プログラムを開始する
handle_input()
