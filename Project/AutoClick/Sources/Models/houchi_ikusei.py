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

sys.path.append("../Common")
import rename
import log


#育成前のstatusの座標
data1_xy = [
        [130, 193,   0 ,  30],      #y1, y2, x1, x2
        [130, 193,  30 ,  60],
        [130 ,193,  60 ,  90],
        [130 ,193,  90 , 120]
] 
#育成後のstatusの座標
data2_xy = [
        [348, 416,   0 ,  30],
        [348, 416,  30 ,  60],
        [348, 416,  60 ,  90],
        [348, 416,  90 , 120]
]
#C級育成、B級育成ボタンの座標
tapxy=[
        [200 , 700],     #c級/cancel
        [380 , 700]      #b級/accept
]

nurture_rank    #育成Rank b/c
data_rate=[1,1,1,1] #筋力、敏捷、知力、体力
loop_number=1

param_zero = list()

def main(args):
    print("init")
    init(args)
    print("ikusei")
    
    exec_ikusei(nurture_rank,data,loop_number)
    print("result")
    show_result()
    os.system("pause")

def init(args):
    global nurture_rank
    global data_rate

    for i in range(args)
        if 1<i:
            data_rate[i-1]=args[i]
        else
            loop_number=args[6]
            nurture_rank=args[1]
    set_data_xy()
    set_tap_xy()


def exec_ikusei(nurture_rank,data,loop_number):
    print("---script start---")
    print(nature_rank + ","+ args[1] + "," + args[6])
    
    for i in range(loop_number):
        print("%d/%d" %(i+1,int(loop_number)))

        if(nurture_rank == 'c'):
                tap(0)
        else:
                tap(1)
        
        calcStatus.ocr_failure_cnt = 0
        getStatus()

        calcStatus(float(args[2]),float(args[3]),float(args[4]),float(args[5]))
        print("-----\n")
    print("---script end---")

def set_data_xy(data1_x=130,
                data1_y=500,data2_x = 348, data2_y = 500, width=60, height=30):

    for i in range(4):
        data1_xy[i][0] = int(data1_x)
        data1_xy[i][1] = int(data1_x + width)
        data1_xy[i][2] = int(data1_y)
        data1_xy[i][3] = int(data1_y + height)
        data2_xy[i][0] = int(data2_x)
        data2_xy[i][1] = int(data2_x + width)
        data2_xy[i][2] = int(data2_y)
        data2_xy[i][3] = int(data2_y + height)

def set_tap_xy(click1_x=200,click1_y=700,click2_x = 380,click2_y = 700):
    tapxy[0][0] = int(click1_x)
    tapxy[0][1] = int(click1_y)
    tapxy[1][0] = int(click2_x)
    tapxy[1][1] = int(click2_y)

def tap(n):
    pyautogui.click(tapxy[n][0], tapxy[n][1])

def getStatus():
    #画像をscreen captureする
    subprocess.call("nox_adb -s %s exec-out screencap -p > screen_1.png" % (dev_addr), shell=True, cwd=ss_dir)
    
    #画像をimgに読み込む
    img = cv2.imread(r"%s\screen_1.png" %(ss_dir))
    #cvtColorでグレースケール画像化し、thresholdで2値化する。
    ret, img_gray = cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 160, 255, cv2.THRESH_BINARY)
    #ret, img_gray = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
    for i in range(4):
        #imageのtrimming(img[top : bottom, left : right])
        cv2.imwrite(pre_ss+str(i)+".png", 
                    img_gray[preStatusxy[i][0]:preStatusxy[i][1], preStatusxy[i][2]:preStatusxy[i][3]])
        cv2.imwrite(ss+str(i)+".png", 
                    img_gray[statusxy[i][0]:statusxy[i][1], statusxy[i][2]:statusxy[i][3]])

    time.sleep(SEC_WAIT_GET_STATUS)


def calcStatus(a,b,c,d):
    while(1):
        param = list()
        for i in range(4):
            param.append(
                tool.image_to_string(
                Image.open(ss+str(i)+".png"),
                lang="eng",
                builder=builder
                ).replace(".", "")
            )
        #print(preParam)
        #print(param)
        print("param:"+param[0]+","+param[1]+","+param[2]+","+param[3])
        print("calcStatus:"+calcStatus.preParam[0]+","+calcStatus.preParam[1]+","+calcStatus.preParam[2]+","+calcStatus.preParam[3])
        try:
            calc = (float(param[0]) - float(calcStatus.preParam[0])) * a \
                        + (float(param[1]) - float(calcStatus.preParam[1])) * b \
                        + (float(param[2]) - float(calcStatus.preParam[2])) * c \
                        + (float(param[3]) - float(calcStatus.preParam[3])) * d
        except ValueError:
            print("warn: 育成ステータスが読み込めません")
            img = cv2.imread(r"%s\screen_1.png" %(ss_dir))
            img_bgr = img[tapxy[0][1], tapxy[0][0], 2]
            time.sleep(SEC_RETRY_GET_STATUS_INTERVAL)
            if img_bgr > 150:
                getStatus()
                continue
            else:
                return

        print("筋力(%.2f)：%d\t(%s -> %s)\n敏捷(%.2f)：%d\t(%s -> %s)\n知力(%.2f)：%d\t(%s -> %s)\n体力(%.2f)：%d\t(%s -> %s)" %(
                    a,int(param[0]) - int(calcStatus.preParam[0]), calcStatus.preParam[0], param[0],
                    b, int(param[1]) - int(calcStatus.preParam[1]), calcStatus.preParam[1], param[1],
                    c, int(param[2]) - int(calcStatus.preParam[2]), calcStatus.preParam[2], param[2],
                    d, int(param[3]) - int(calcStatus.preParam[3]), calcStatus.preParam[3], param[3]))
        print("筋力：{:+}、敏捷：{:+}、知力：{:+}、体力：{:+}". format(int(param[0]) - int(param_zero[0]),
                                                                int(param[1]) - int(param_zero[1]),
                                                                int(param[2]) - int(param_zero[2]),
                                                                int(param[3]) - int(param_zero[3])))
        
        #誤認識用
        flg_ocr_failure = 0
        for i in range(4):
            if abs(int(param[i]) - int(calcStatus.preParam[i])) > 20: #C級、B級の育成変動値は20を超えない
                calcStatus.ocr_failure_cnt += 1
                if calcStatus.ocr_failure_cnt > MAX_OCR_RETRY:
                    print("warn: OCRリトライ回数超過、ステータスリセットのため育成確定します")
                    tap(1)
                    flg_ocr_failure = 2   
                else:
                    print("warn: OCR誤認識検知、ステータスを再読み込みします...%d" %(calcStatus.ocr_failure_cnt))
                    time.sleep(SEC_RETRY_OCR_INTERVAL)
                    flg_ocr_failure = 1
                getStatus()
                calcStatus.preParam = list()
                for i in range(4):
                    calcStatus.preParam.append(
                        tool.image_to_string(
                            Image.open(pre_ss+str(i)+".png"),
                            lang="eng",
                            builder=builder
                        ).replace(".", "")
                    )
                break
        if flg_ocr_failure == 1:
            continue
        elif flg_ocr_failure == 2:
            break


        print("Calculation Res: %.2f" %calc)
        if (calc > 0):
            print("Accept")
            tap(1)
            for i in range(4):
                calcStatus.preParam[i] = param[i]

        else:
            print("Cancel")
            tap(0)
        break

if __name__ == '__main__':    
    main(sys.argv)
