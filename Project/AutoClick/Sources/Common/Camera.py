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
    #cv2.imshow('frame', frame)
    # ウィンドウをすべて閉じます
    #cv2.destroyAllWindows()
    cap.release()

    # 書き込みが失敗した場合、エラーメッセージを表示して異常終了する
    if not result:
        print("Error: failed to write file")
        return False

    return True

def main(argument_dictionary):
    
    file_path = argument_dictionary.get("file_path","")
    if(file_path != ""):
        result = capture(file_path)
    else:
        result = False
    result_dictionary={"result" : result}
    FunctionUtility.Result(result_dictionary)

if __name__ == '__main__':
    # Defaultの辞書Data
    default_dictionary = {
        "file_path": "./execute.png"
    }
    argument_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    main(argument_dictionary)
