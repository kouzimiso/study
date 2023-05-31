import cv2
import sys
import JSON_Control

def capture(file_path):
    # 内蔵カメラを使用する場合、引数は0に設定します
    cap = cv2.VideoCapture(0)
    # カメラから1フレーム取得する
    ret, frame = cap.read()
    
    # カメラからのフレームが無効の場合、処理を中断します
    if not ret:
        return False
    cv2.imwrite(file_path,frame)    
    # フレームを表示する
    #cv2.imshow('frame', frame)
    # ウィンドウをすべて閉じます
    #cv2.destroyAllWindows()
    cap.release()

    return True

if __name__ == '__main__':

    try:
        json_str = sys.argv[1]
    except IndexError:
        # 引数が指定されていない場合には、以下のコメントを出力します
        print("JSON形式の文字列を指定してください")
        sys.exit()

    json_dictionary = JSON_Control.JsonToDictionary(json_str)
    
    file_path = json_dictionary.get("file_path","")
    if(file_path != ""):
        capture(file_path)
