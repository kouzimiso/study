## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import sys
import os
import datetime
import time
import pyautogui
import cv2
import glob
import signal
import subprocess
from enum import Enum
import PIL

sys.path.append("./Common")
sys.path.append("./Models")
sys.path.append("./ViewModels")
sys.path.append("./Views")
import ocr
import weekday
import log
import image_control
import auto


#Program設定関係(必要に応じて変更)

#log関係
message_list=[]
logfile_path='../Log/log_wafer.txt'

#アニメーションするボタンが押せない対策
#画像を探してずらした位置をクリックする設定。{画像Path:ずらす位置}の形式で記述する。
x_offset_dictionary= {'../image_ikusei\Click9254.png' : "0"}
y_offset_dictionary= {'../image_ikusei\Click9254.png' : "-60",'../image_ikusei\Click2003.png' : "-30",'./image_ikusei\Click9204.png' : "-60",'./image_event2\Click9254.png' : "-60",'./image_event2\Click2003.png' : "-30",'./image_event2\Click9204.png' : "-60"}
        
def Log_MessageFormat(message):
    log_message='[' + str(datetime.datetime.now())+']' + message +'\n'
    return log_message

#LogをListに貯める動作。
def Log_MessageAdd(message_list,message):
    print(message)
    message_list.append(Log_MessageFormat(message))

#MessageをFileに書き込む
def Write_Message(file_path,message):
    file = open(file_path,'a')
    file.write(message)
    file.close()

#Message ListをFileに書き込む
def Write_MessageList(file_path,message_list):
    file = open(file_path,'a')
    file.writelines(message_list)
    file.close()

#強制終了時処理（Ctrl+C）
def EndProcess():
    Write_MessageList(logfile_path , message_list)
    message_list.clear()
    subprocess.Popen(["notepad",logfile_path])

#signal処理
def Signal_Handler(signal_number,frame) -> None:
    sys.exit(1)



#Main Program実行部
def main():
    signal.signal(signal.SIGTERM, Signal_Handler)
    try:
        while 1:
            sequence = auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 3, 0, '../Images/wafer/*.png', 0, 0.93, True)
            result_action = auto.Images_Action_ByInformation(sequence, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
            Write_MessageList(logfile_path , message_list)
            message_list.clear()
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        EndProcess()
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        

if __name__ == "__main__":
    sys.exit(main())
