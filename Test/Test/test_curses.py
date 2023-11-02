import curses
import os
def main(stdscr):
    # 初期化
    os.system('')  # 必須。WindowsでANSIエスケープシーケンスを有効にする
    stdscr.clear()

    # 辞書を初期化
    data = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4'
    }

    # ユーザーが選択した項目を格納する変数
    selected_item = 0

    # 繰り返し処理
    while True:
        # 画面を更新する
        stdscr.clear()

        # タイトルを描画する
        stdscr.addstr(0, 0, 'Dictionary Editor', curses.A_BOLD)

        # 項目を描画する
        for i, key in enumerate(data.keys()):
            if i == selected_item:
                # 選択された項目は反転表示する
                stdscr.addstr(i + 2, 0, key + ': ' + data[key], curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 0, key + ': ' + data[key])

        # ユーザーの入力を待つ
        key = stdscr.getch()

        # ユーザーが上矢印キーを押した場合
        if key == curses.KEY_UP:
            selected_item = max(0, selected_item - 1)

        # ユーザーが下矢印キーを押した場合
        elif key == curses.KEY_DOWN:
            selected_item = min(len(data) - 1, selected_item + 1)

        # ユーザーがエンターキーを押した場合
        elif key == curses.KEY_ENTER or key in [10, 13]:
            # 選択された項目を編集する
            key_list = list(data.keys())
            selected_key = key_list[selected_item]
            stdscr.addstr(len(data) + 3, 0, 'Edit value for ' + selected_key + ': ')
            value = stdscr.getstr().decode('utf-8')
            data[selected_key] = value

        # ユーザーがESCキーを押した場合
        elif key == 27:
            break

    # 画面を初期化する
    stdscr.clear()
    curses.curs_set(1)

# cursesモードでプログラムを開始する
curses.wrapper(main)
