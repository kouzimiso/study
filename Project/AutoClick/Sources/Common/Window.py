import pygetwindow
import pyautogui
import FunctionUtility



def close_window_by_name(window_name,flag_exact_match = True):
    matching_windows = pygetwindow.getWindowsWithTitle(window_name)
    if not matching_windows:
        return False
    for window in matching_windows:
        result = False
        window_title = window.title
        if flag_exact_match == True:
            if window_name == window_title:
                window.close()
                result = True
        else:
            if window_name in window_title:
                #完全一致ではない場合は部分一致する全てのWindowを閉じる。
                window.close()
                result = True
    return result

def close_window_by_selection(matching_windows):
    if not matching_windows:
        print("指定した文字列を含むウィンドウが見つかりません。")
        return False
    
    print("以下のウィンドウが見つかりました:")
    for idx, window_title in enumerate(matching_windows, start=1):
        print(f"{idx}. {window_title}")
    
    try:
        choice = int(input("閉じたいウィンドウの番号を選択してください (0 でキャンセル): "))
        
        if choice == 0:
            return False
        
        if 1 <= choice <= len(matching_windows):
            result = close_window_by_name(matching_windows[choice - 1])
            if result :
                print(f"{matching_windows[choice - 1]} を閉じました。")
            else:
                print(f"Windowを閉じる際にErrorが発生しました。")
            return result
        else:
            print("無効な選択です。正しい番号を選んでください。")
            return False
    except ValueError:
        print("無効な入力です。数値を入力してください。")
        return False

# Defaultの辞書Dataを設定
default_dictionary = {
    "action":"DELETE",
    "target_text":"text of close window", # 閉じたいウィンドウを含む文字列をここに入力してください 
    "flag_exact_match":True
}
# 辞書設定の読込と機能実行
def Execute(setting_dictionary):
    #設定の読込
    action = setting_dictionary.get("action","")
    target_text = setting_dictionary.get("target_text","")
    flag_exact_match = setting_dictionary.get("flag_exact_match",True)
    #機能実行 
    result_dictionary = {}
    if action == "DELETE":
        result = close_window_by_name(target_text,flag_exact_match)
        if result == False:
            matching_windows =  pygetwindow.getWindowsWithTitle(target_text)   
            result = close_window_by_selection(matching_windows)
    result_dictionary["result"]= result
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    setting_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    result_dictionary = Execute(setting_dictionary)
    FunctionUtility.Result(result_dictionary)

if __name__ == '__main__':
    main()

