import sys
import cv2
import FunctionUtility
import Rename

def capture(file_path):
    # 内蔵カメラを使用する場合、引数は0に設定します
    cap = cv2.VideoCapture(0)
    # カメラから1フレーム取得する
    ret, frame = cap.read()
    
    # カメラからのフレームが無効の場合、処理を中断します
    if not ret:
        return False
    file_path = Rename.duplicate_rename(file_path)
    result = cv2.imwrite(file_path,frame)
    # フレームを表示する
    #cv2.imshow('frame', frame)eckDay
    # ウィンドウをすべて閉じます
    #cv2.destroyAllWindows()
    cap.release()

    # 書き込みが失敗した場合、エラーメッセージを表示して異常終了する
    if not result:
        print("Error: failed to write file")
        return False

    return True
# Defaultの辞書Dataを設定
default_dictionary = {
    "file_path": "./execute.png"
}
# 辞書設定の読込と機能実行
def Execute(settings_dictionary):
    #設定の読込
    file_path = settings_dictionary.get("file_path","")
    #機能実行 
    result_dictionary = {}
    if(file_path != ""):
        result = capture(file_path)
    else:
        result = False
    result_dictionary["result"] = result
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    settings_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    result_dictionary = Execute(settings_dictionary)
    FunctionUtility.Result(result_dictionary)

if __name__ == '__main__':
    main()

