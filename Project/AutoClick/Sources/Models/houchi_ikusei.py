## $python 画像自動Click ##
# 設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import time
import datetime
import sys
import os
import pyautogui
import PIL
import cv2
import glob
import subprocess
import signal
from enum import Enum

sys.path.append("./Common")
sys.path.append("../Common")
import Rename
import Log
import ADB
import ImageControl
import OCR
import Calculation

#画像保存Folder

device_address = "0.0.0.0"
MAX_OCR_RETRY=3

#育成前のstatusの座標(x1, y1, x2, y2)
data1_xy = [] 
#育成後のstatusの座標(x1, y1, x2, y2)
data2_xy = []
#C級育成、B級育成ボタンの座標
tapxy=[
        [400 , 1480],     #c級/cancel x,y
        [760 , 1480]      #b級/accept x,y
]
screenshot_file="tmp\screen_1.png"
pre_ss_files=["tmp\pre_status0.png","tmp\pre_status1.png","tmp\pre_status2.png","tmp\pre_status3.png"]
ss_files=["tmp\status0.png","tmp\status1.png","tmp\status2.png","tmp\status3.png"]

nurture_rank="c"    #育成Rank b/c
data_rate=[0.5,0,1,0.1] #筋力、敏捷、知力、体力
loop_number=1000

param_zero = list()

def main(args):
    print("init")
    init(args)
    exec_input()
    print("execute")
    exec_Growth(nurture_rank,data_rate,loop_number)
    print("result")
    show_result()
    os.system("pause")

def init(args):
    global nurture_rank
    global data_rate
    global data1_xy
    global data2_xy
    
    print("---Initial Setting---")
    print("引数:{b/c育成丹 筋 敏 知 体 回数")
    if 6 <= len(args):
        #args=["c",1,1,1,1,1]
        nurture_rank=args[0]
        data_rate[0]=args[1]
        data_rate[1]=args[2]
        data_rate[2]=args[3]
        data_rate[3]=args[4]
        loop_number=args[5]
    data1_xy=set_data_xy(270,890,126,60)#(x1, y1, x2, y2)
    data2_xy=set_data_xy(696,890,126,60)#(x1, y1, x2, y2)

def exec_input():
    global param_zero
    capture_data()
    ocr_instance = OCR.OCR()
    ocr_instance.Setting_BuilderDigits()
    param_zero = ocr_instance.Recognition_ByFilePathList(pre_ss_files, "eng")
    #calcStatus.preParam = param_zero
    calcStatus.preParam = list()
    for parameter in param_zero:
        calcStatus.preParam.append(parameter)

def exec_Growth(nurture_rank,data_rate,loop_number):
    print("---script start---")
    
    for loop in range(loop_number):
        print("%d/%d" %(loop+1,int(loop_number)))

        if(nurture_rank == 'c'):
                tap(0)
        else:
                tap(1)
        
        calcStatus.ocr_failure_cnt = 0
        capture_data()
        calcStatus(float(data_rate[0]),float(data_rate[1]),float(data_rate[2]),float(data_rate[3]))
        print("-----\n")
    print("---script end---")

def show_result():
    capture_data()
    ocr_instance = OCR.OCR()
    ocr_instance.Setting_BuilderDigits()
    param_end = ocr_instance.Recognition_ByFilePathList(pre_ss_files, "eng")
    print("筋力：{:+}、敏捷：{:+}、知力：{:+}、体力：{:+}". format(int(param_end[0]) - int(param_zero[0]),
                                                                int(param_end[1]) - int(param_zero[1]),
                                                                int(param_end[2]) - int(param_zero[2]),
                                                                int(param_end[3]) - int(param_zero[3])))
def set_data_xy(data_x=130,
                data_y=500, width=60, height=30):
    data_xy=[
        [0,0,0,0],
        [0,0,0,0],
        [0,0,0,0],
        [0,0,0,0]
        ]
        
    for loop in range(4):
        if loop ==0:
            data_xy[loop][0] = int(data_x)
            data_xy[loop][1] = int(data_y)
            data_xy[loop][2] = int(data_x + width)
            data_xy[loop][3] = int(data_y + height)
        else:
            data_xy[loop][0] = data_xy[loop-1][0]
            data_xy[loop][1] = data_xy[loop-1][1]+ height
            data_xy[loop][2] = data_xy[loop-1][2]
            data_xy[loop][3] = data_xy[loop-1][3]+ height
    return data_xy

def tap(n):
    #pyautogui.click(tapxy[n][0], tapxy[n][1])
    ADB.Tap(device_address , tapxy[n][0] , tapxy[n][1])

def capture_data():
    global device_address
    message_list=[]
    #ImageControl.Image_Capture(screenshot_file)
    #画像をscreen captureする
    device_address = ADB.Get_DeviceAddress()
    screen_size = ADB.Get_ScreenSize(device_address)
    Log.Log_MessageAdd(message_list,str(screen_size))
    ADB.ScreenCapture(device_address,screenshot_file)
    #画像をimgに読み込む
    img = cv2.imread(screenshot_file)
    #cvtColorでグレースケール画像化し、thresholdで2値化する。
    ret, img_gray = cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 160, 255, cv2.THRESH_BINARY)
    #ret, img_gray = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)

    #imageのtrimming(img[top : bottom, left : right])
    #ScreenShootのData部分を画像に保存する    
    ImageControl.CVImageCrop_ByList(img_gray,pre_ss_files,data1_xy)
    ImageControl.CVImageCrop_ByList(img_gray,ss_files,data2_xy)



def calcStatus(a,b,c,d):
    ocr_instance = OCR.OCR()
    ocr_instance.Setting_BuilderDigits()
    while(1):
        #画像FileListのOCR結果Listを取得
        param = ocr_instance.Recognition_ByFilePathList(ss_files, "eng")
        print("param:"+param[0]+","+param[1]+","+param[2]+","+param[3])
        print("calcStatus:"+calcStatus.preParam[0]+","+calcStatus.preParam[1]+","+calcStatus.preParam[2]+","+calcStatus.preParam[3])
        list_label=["筋力","敏捷","知力","体力"]
        #前回との差分による評価を計算
        try:
            calc = Calculation.differential_rating_value(param,calcStatus.preParam,data_rate,list_label)
        except ValueError:
            print("warn: 育成ステータスが読み込めません")
            #img = cv2.imread(r"%s\screen_1.png" %(ss_dir))
            img = cv2.imread(screenshot_file)
            
            img_bgr = img[tapxy[0][1], tapxy[0][0], 2]
            if img_bgr > 150:
                capture_data()
                continue
            else:
                return
        print("筋力：{:+}、敏捷：{:+}、知力：{:+}、体力：{:+}". format(int(param[0]) - int(param_zero[0]),
                                                                int(param[1]) - int(param_zero[1]),
                                                                int(param[2]) - int(param_zero[2]),
                                                                int(param[3]) - int(param_zero[3])))
        
        #誤認識用
        flg_ocr_failure = 0
        for loop in range(4):
            if abs(int(param[loop]) - int(calcStatus.preParam[loop])) > 20: #C級、B級の育成変動値は20を超えない
                calcStatus.ocr_failure_cnt += 1
                if calcStatus.ocr_failure_cnt > MAX_OCR_RETRY:
                    print("warn: OCRリトライ回数超過、ステータスリセットのため育成確定します")
                    tap(1)
                    flg_ocr_failure = 2   
                else:
                    print("warn: OCR誤認識検知、ステータスを再読み込みします...%d" %(calcStatus.ocr_failure_cnt))
                    flg_ocr_failure = 1
                capture_data()
                calcStatus.preParam = list()
                ocr_instance = OCR.OCR()
                ocr_instance.Setting_BuilderDigits()
                parameter = ocr_instance.Recognition_ByFilePathList(pre_ss_files, "eng")
                calcStatus.preParam = parameter

                break
        if flg_ocr_failure == 1:
            continue
        elif flg_ocr_failure == 2:
            break


        print("Calculation Res: %.2f" %calc)
        if (calc > 0):
            print("Accept")
            tap(1)
            for loop in range(4):
                calcStatus.preParam[loop] = param[loop]

        else:
            print("Cancel")
            tap(0)
        break

if __name__ == '__main__':    
    main(sys.argv)
