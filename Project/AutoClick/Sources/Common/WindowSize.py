import pygetwindow as gw
import json

def get_application_window_sizes():
    # 実行中のアプリケーションの一覧を取得
    app_list = gw.getAllTitles()

    # ウィンドウごとにサイズを取得し、辞書に格納
    window_sizes = {}
    for app_title in app_list:
        try:
            window = gw.getWindowsWithTitle(app_title)[0]

            # ウィンドウのサイズを取得
            window_sizes[app_title] = {
                'Width': window.width,
                'Height': window.height
            }
        except (IndexError, AttributeError):
            # ウィンドウが見つからないか、サイズがない場合は無視
            pass
    
    return window_sizes

def print_dictionary_contents(dictionary):
    # 辞書の内容をプリントする関数
    for key, value in dictionary.items():
        print(key)
        for k, v in value.items():
            print(f"  {k}: {v}")
        print()

def main():
    # アプリケーション一覧とウィンドウサイズ情報を取得
    window_sizes = get_application_window_sizes()

    # 辞書の内容をコンソールに表示
    print_dictionary_contents(window_sizes)

    # 結果をJSON形式で出力
    with open('window_sizes.json', 'w') as json_file:
        json.dump(window_sizes, json_file, indent=4)

    print("ウィンドウサイズ情報を window_sizes.json に保存しました。")

if __name__ == "__main__":
    main()
