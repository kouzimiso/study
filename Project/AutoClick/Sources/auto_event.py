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
import OCR
import Weekday
import Log
import ImageControl
import Auto


#Program設定関係(必要に応じて変更)

#log関係
message_list=[]
logfile_path='../Log/log_event.txt'

action_sequence_start = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 2, 0, '../Images/image_start/Click0*.png', 1.8, 0.93, True)

#アニメーションするボタンが押せない対策
#画像を探してずらした位置をクリックする設定。{画像Path:ずらす位置}の形式で記述する。
x_offset_dictionary= {'../image_grouth\Click9254.png' : "0"}
y_offset_dictionary= {'../image_grouth\Click9254.png' : "-60",'../image_grouth\Click2003.png' : "-30",'./image_grouth\Click9204.png' : "-60",'./image_event2\Click9254.png' : "-60",'./image_event2\Click2003.png' : "-30",'./image_event2\Click9204.png' : "-60"}
        
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


def timecheck_grouth():
    #放置少女育成時間チェック(イベント時にDairy消費防止12:00まで待つ)
    week_day = Weekday.DayOfTheWeek(set_monday=1)
    date_time = datetime.datetime.now()
    #time1 = datetime.time(12,00,00)
    time1 = datetime.time(8,00,00)
    time2 = datetime.time(23,45,00)
    
    day_of_weekday1=week_day.SaturDay
    day_of_weekday2=week_day.SunDay
    check1 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check1:
        message_list.extend(week_day.message_list)
    
    day_of_weekday1=week_day.MonDay
    day_of_weekday2=week_day.MonDay
    week_day.message_list.clear()
    check2 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check2:
        message_list.extend(week_day.message_list)
    
    day_of_weekday1=week_day.TuesDay
    day_of_weekday2=week_day.ThursDay
    week_day.message_list.clear()
    check3 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check3:
        message_list.extend(week_day.message_list)
    
    day_of_weekday1=week_day.FriDay
    day_of_weekday2=week_day.FriDay
    week_day.message_list.clear()
    check4 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check4:
        message_list.extend(week_day.message_list)
    
    flag_execute = check1 or check2  or check3  or check4
    if flag_execute:
        Log_MessageAdd(message_list,"time check" + date_time.strftime ( '%Y 年 %m 月 %d　日　(%A) %H : %M' ))
        Log_MessageAdd(message_list,"test")
    return flag_execute


def timecheck_login():
    #放置少女Login時間チェック
    week_day = Weekday.DayOfTheWeek(set_monday=1)   
    date_time = datetime.datetime.now()
    
    time1 = datetime.time(8,00,00)
    time2 = datetime.time(23,45,00)
    
    day_of_weekday1=week_day.SaturDay
    day_of_weekday2=week_day.SunDay
    check1 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check1:
        message_list.extend(week_day.message_list)
    
    day_of_weekday1=week_day.MonDay
    day_of_weekday2=week_day.MonDay
    week_day.message_list.clear()
    check2 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check2:
        message_list.extend(week_day.message_list)
    
    day_of_weekday1=week_day.TuesDay
    day_of_weekday2=week_day.ThursDay
    week_day.message_list.clear()
    check3 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check3:
        message_list.extend(week_day.message_list)
    
    day_of_weekday1=week_day.FriDay
    day_of_weekday2=week_day.FriDay
    week_day.message_list.clear()
    check4 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check4:
        message_list.extend(week_day.message_list)
        
    flag_execute = check1 or check2  or check3  or check4
    if flag_execute:
        Log_MessageAdd(message_list,"time check" + date_time.strftime ( '%Y 年 %m 月 %d　日　(%A) %H : %M' ))
    return flag_execute

def timecheck_afternoon():
    #19:40-21:45
    if  datetime.time(12,30,0) <= datetime.datetime.now().time() and  datetime.datetime.now().time() <= datetime.time(13,45,0):
        #return True #通常時
        return False #Event時 自動回し優先
    else:
        return False

def timecheck_evening():
    #19:40-21:45
    if  datetime.time(19,40,0) <= datetime.datetime.now().time() and  datetime.datetime.now().time() <=  datetime.time(21,45,0):
        #return True #通常時
        return False #Event時 自動回し優先
    else:
        return False

def highspeed():
    #放置少女2.5倍日 特殊動作
    week_day = Weekday.DayOfTheWeek(set_monday=1)   
    date_time = datetime.datetime.now()
    
    time1 = datetime.time(8,00,00)
    time2 = datetime.time(23,45,00)
    
    day_of_weekday1=week_day.SunDay
    day_of_weekday2=week_day.SunDay
    check1 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check1:
        message_list.extend(week_day.message_list)
    
    day_of_weekday1=week_day.ThursDay
    day_of_weekday2=week_day.ThursDay
    week_day.message_list.clear()
    check2 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check2:
        message_list.extend(week_day.message_list)
        
    day_of_weekday1=week_day.WednesDay
    day_of_weekday2=week_day.WednesDay
    check3 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check3:
        message_list.extend(week_day.message_list)

    day_of_weekday1=week_day.SaturDay
    day_of_weekday2=week_day.SaturDay
    check4 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
    if check4:
        message_list.extend(week_day.message_list)

    flag_execute = check1 or check2 or check3 or check4
    if flag_execute:
        Log.Log_MessageAdd(message_list,"time check" + date_time.strftime ( '%Y 年 %m 月 %d　日　(%A) %H : %M' ))

        file_path = '../Images/image_item/*.png'
        sequence_item = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 1, 0, file_path, 0.8, 0.93, False)
        result_action = Auto.Images_Action_ByInformation(sequence_item, x_offset_dictionary, y_offset_dictionary)

        file_path = '../Images/image_highspeed/*.png'
        sequence_highspeed=Auto.RecognitionInformation(Auto.ACTION.CLICK ,Auto.RESULT.OK, Auto.END_ACTION.CONTINUE ,1, 0 ,file_path , 0.8 , 0.93 , True)
        result_action = Auto.Images_Action_ByInformation(sequence_highspeed,x_offset_dictionary,y_offset_dictionary)
        
        result_start = Auto.Images_Action_ByInformation(action_sequence_start, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting

   

def ocr_sequence():
    info_message_list=[]
    info_logfile_path='../log/log_information.txt'
    #画面Captureの文字認識
    ocr_instance = OCR.OCR()
    sequence_Information0 = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 1, 0, '../Images/images/image_Information0/*.png', 0.8, 0.93, True)
    result_action = Auto.Images_Action_ByInformation(sequence_Information0, x_offset_dictionary, y_offset_dictionary)
    sequence_Information1 = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_Information1/*.png', 0.8, 0.93, True)
    result_action = Auto.Images_Action_ByInformation(sequence_Information1, x_offset_dictionary, y_offset_dictionary)
    file_path = "../Images/image_information/screen_capture1.png"
    file_path2 = "../Images/image_information/screen_capture_Comment.png"
    bbox_w=700
    bbox_h=600
    bbox_x=600
    bbox_y=0
    PIL.ImageGrab.grab(bbox=(bbox_x,  bbox_y,bbox_x + bbox_w , bbox_y + bbox_h)).save(file_path)
    image = ImageControl.CropAndAlign_ByFilePath(file_path,
        0,
        200,
        500,
        100,
        ImageControl.HOLIZONTAL_ALIGN.CENTER,
        ImageControl.VIRTICAL_ALIGN.MIDDLE
        )
    image.save(file_path2)
    ocr_instance.Setting_BuilderText(6)
    text=ocr_instance.Recognition_ByFilePath(file_path2,"jpn")
    Log.Log_MessageAdd(info_message_list,"Comment:\n"+text)

    sequence_Information0 = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_Information0/*.png', 0.8, 0.93, True)
    result_action = Auto.Images_Action_ByInformation(sequence_Information0, x_offset_dictionary, y_offset_dictionary)
    sequence_Information2 = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_Information2/*.png', 0.8, 0.93, True)
    result_action = Auto.Images_Action_ByInformation(sequence_Information2, x_offset_dictionary, y_offset_dictionary)
    if result_action:

        sequence_Information2 = Auto.RecognitionInformation(Auto.ACTION.CLICK ,Auto.RESULT.OK, Auto.END_ACTION.CONTINUE ,1, 0 ,'./Images/image_Information2/*.png' , 0.8 , 0.93 , True)
        result_action = Auto.Images_Action_ByInformation( sequence_Information2,x_offset_dictionary,y_offset_dictionary)
        file_path = "../Images/image_information/screen_capture2.png"
        file_path2 = "../Images/image_information/screen_capture_Name.png"
        file_path3 = "../Images/image_information/screen_capture_Money.png"
        file_path4 = "../Images/image_information/screen_capture_Level.png"
        bbox_w=700
        bbox_h=600
        bbox_x=600
        bbox_y=0
        PIL.ImageGrab.grab(bbox=(bbox_x,  bbox_y,bbox_x + bbox_w , bbox_y + bbox_h)).save(file_path)
        image = ImageControl.CropAndAlign_ByFilePath(file_path,
            100,
            45,
            140,
            70,
            ImageControl.HOLIZONTAL_ALIGN.LEFT,
            ImageControl.VIRTICAL_ALIGN.TOP
            )
        image.save(file_path2)
        image = ImageControl.CropAndAlign_ByFilePath(file_path,
            480,
            45,
            100,
            60,
            ImageControl.HOLIZONTAL_ALIGN.LEFT,
            ImageControl.VIRTICAL_ALIGN.TOP
            )
        image.save(file_path3)
        image = ImageControl.CropAndAlign_ByFilePath(file_path,
            0,
            110,
            150,
            30,
            ImageControl.HOLIZONTAL_ALIGN.CENTER,
            ImageControl.VIRTICAL_ALIGN.TOP
            )
        image.save(file_path4)
        
        ocr_instance.Setting_BuilderText(6)
        text=ocr_instance.Recognition_ByFilePath(file_path2,"jpn")
        Log.Log_MessageAdd(info_message_list,"Name:"+text)
        text=ocr_instance.Recognition_ByFilePath(file_path3,"jpn")
        Log.Log_MessageAdd(info_message_list,"Money:"+text)
        text=ocr_instance.Recognition_ByFilePath(file_path4,"jpn")
        Log.Log_MessageAdd(info_message_list,"Level:"+text)
    Write_MessageList(info_logfile_path , info_message_list)
    info_message_list.clear()
    
    for loop1 in range(3,13):
        ocr_instance.Setting_BuilderText(loop1)
        #text=ocr_instance.Recognition(image,"jpn")
        text=ocr_instance.Recognition_ByFilePath(file_path2,"jpn")
        Log.Log_MessageAdd(message_list,"ocr" + str(loop1) + ":\n" + text)
        text=ocr_instance.Recognition_ByFilePath(file_path3,"jpn")
        Log.Log_MessageAdd(message_list,"ocr" + str(loop1) + ":\n" + text)
        text=ocr_instance.Recognition_ByFilePath(file_path4,"jpn")
        Log.Log_MessageAdd(message_list,"ocr" + str(loop1) + ":\n" + text)

def UnderWare():
    for i in range(2):
        action_underware = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE,3, 0, '../Images/UnderWare/Click00*.png', 0, 0.93, True)
        result_action = Auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
        for i in range(10):
            action_underware = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE ,2, 2, '../Images/UnderWare/Click010*.png', 0, 0.93, True)
            result_action = Auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            action_underware = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.BREAK ,3, 2, '../Images/UnderWare/Click011*.png', 0, 0.97, True)
            result_action = Auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            #action_underware = RecognitionInformation(ACTION.CLICK, RESULT.OK, END_ACTION.BREAK ,1, 20, '../Images/UnderWare/Click012*.png', 0, 0.85, True)
            #result_action = Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            #action_underware = RecognitionInformation(ACTION.CLICK, RESULT.OK, END_ACTION.BREAK ,1, 20, '../Images/UnderWare/Click013*.png', 0, 0.85, True)
            #result_action = Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            action_underware = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.ALL_OK, Auto.END_ACTION.FOLDER_END_BREAK ,1, 0, '../Images/UnderWare/Click014*.png', 0, 0.93, True)
            result_action = Auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
        action_underware = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 7, 2, '../Images/UnderWare/Click02*.png', 0, 0.93, True)
        result_action = Auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)


#Main Program実行部
def main():
    signal.signal(signal.SIGTERM, Signal_Handler)

    action_sequence_waiting = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.NG, Auto.END_ACTION.CONTINUE, 4, 20, '../Images/image_waiting/*.png', 4, 0.99, False)
    action_sequence_start = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_start/*.png', 1.8, 0.93, True)
    action_sequence_main = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 4, 0, '../Images/image/*.png', 0.5, 0.93, True)
    action_sequence_event = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 3, 0, '../Images/image_event/*.png', 0.5, 0.93, True)
    action_sequence_event2 = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 2, 2, '../Images/image_event2/*.png', 0.8, 0.93, True)
    #result = Auto.Images_Action_ByInformation(action_sequence_waiting, x_offset_dictionary, y_offset_dictionary)
    #result = Auto.Images_Action_ByInformation(action_sequence_start, x_offset_dictionary, y_offset_dictionary)
    #result = Auto.Images_Action_ByInformation(action_sequence_main, x_offset_dictionary, y_offset_dictionary)
    result = Auto.Images_Action_ByInformation(action_sequence_event, x_offset_dictionary, y_offset_dictionary)
    result = Auto.Images_Action_ByInformation(action_sequence_event2, x_offset_dictionary, y_offset_dictionary)
    try:

        #UnderWare()
        highspeed()
            
        #while 1:
            #action_mementomori = RecognitionInformation(ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.CONTINUE,1, 3, '../Images/mementomori/Click00*.png', 1.8, 0.95, True)
            #result_action = Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
            #if result_action:
            #        
            #    action_mementomori = RecognitionInformation(ACTION.DOUBLE_CLICK, RESULT.NG, END_ACTION.CONTINUE,25, 100, '../Images/mementomori/Click05*.png', 5, 0.95, True)
            #    result_action = Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
            #
            #    action_mementomori = RecognitionInformation(ACTION.CLICK, RESULT.NG, END_ACTION.CONTINUE, 50, 3, '../Images/mementomori/Click1*.png', 1.8, 0.95, True)
            #    result_action = Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
        
        
        Log.Log_MessageAdd(message_list,"OCR start")
        ocr_sequence()
        #action_kyoudou1=RecognitionInformation(ACTION.CLICK ,RESULT.OK, END_ACTION.CONTINUE ,10, 0 ,'../Images/image_kyoudou1/*.png' , 0.8 , 0.93 , True)
        #result_action = Images_Action_ByInformation(action_kyoudou1,x_offset_dictionary,y_offset_dictionary)
        #if result_action:
        #    action_kyoudou2=RecognitionInformation(ACTION.CLICK ,RESULT.NG, END_ACTION.FOLDER_END_BREAK, 300,0,'../Images/image_kyoudou2/*.png' , 0.3 , 0.93 , True)
        #    result_action = Images_Action_ByInformation(action_kyoudou2,x_offset_dictionary,y_offset_dictionary)
        action_sequence_event = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 3, 0, '../Images/image_event/*.png', 0.5, 0.93, True)
        action_sequence_grouth = Auto.RecognitionInformation(Auto.ACTION.CLICK, Auto.RESULT.OK, Auto.END_ACTION.CONTINUE, 3, 1, '../Images/image_grouth/*.png', 1.8, 0.93, True)
        result_action = Auto.Images_Action_ByInformation(action_sequence_event, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
        result_action = Auto.Images_Action_ByInformation(action_sequence_grouth, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
        highspeed()

        Log.Log_MessageAdd(message_list,"Event2 start")
        action_sequence_event2 = Auto.RecognitionInformation(Auto.ACTION.CLICK ,Auto.RESULT.OK, Auto.END_ACTION.CONTINUE ,10, 0 ,'../Images/image_event2/*.png' , 0.8 , 0.93 , True)
        result_action = Auto.Images_Action_ByInformation(action_sequence_event2,x_offset_dictionary,y_offset_dictionary)
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
