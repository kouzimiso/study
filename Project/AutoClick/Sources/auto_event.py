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

class END_ACTION(Enum):
    BREAK = 0
    FOLDER_END_BREAK = 1
    CONTINUE = 2

class RESULT(Enum):
    NG= 0
    OK= 1
    ALL_OK = 2

    
class ACTION(Enum):
    NONE= 0
    CLICK= 1
    DOUBLE_CLICK = 2

#画像認識情報定義
class RecognitionInfomation:
    def __init__(self  ,action , end_condition, end_action , execute_number, retry_number, image_path  , interval_time , recognition_confidence ,recognition_grayscale ):
        #処理
        self.action = action
        #終了条件
        self.end_condition = end_condition
        #実行回数
        self.execute_number = execute_number
        #再試行回数
        self.retry_number = retry_number
        #終了処理
        self.end_action = end_action
        #クリックする画像を保存するフォルダ
        self.image_path = image_path
        #画像をClickした後の待ち時間(秒)
        self.interval_time = interval_time
        #画像認識のあいまい設定
        self.recognition_confidence = recognition_confidence
        #GrayScale設定(高速化)
        self.recognition_grayscale = recognition_grayscale

#Program設定関係(必要に応じて変更)

#log関係
message_list=[]
logfile_path='../Log/log_event.txt'


#画像認識動作設定
action_sequence_test=RecognitionInfomation(ACTION.CLICK ,RESULT.OK, END_ACTION.CONTINUE ,1, 0 ,'./Test/*.png' , 0.8 , 0.93 , True)


search_icon1_sequence = []
search_icon1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image00/*.png', 10, 0.99, True))
search_icon1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image01/*.png', 10, 0.97, True))

select_server1_sequence = []
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer01/*.png', 1.8, 0.8, True))
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer02/*.png', 1.8, 0.8, True))
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer03/*.png', 1.8, 0.8, True))
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer04/*.png', 1.8, 0.8, True))
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer05/*.png', 1.8, 0.8, True))
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer06/*.png', 1.8, 0.8, True))
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer07/*.png', 1.8, 0.8, True))
select_server1_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer08/*.png', 1.8, 0.8, True))


search_icon2_sequence = []
search_icon2_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image00/*.png', 10, 0.99, True))
search_icon2_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image01/*.png', 10, 0.97, True))
search_icon2_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image02/*.png', 10, 0.99, True))
search_icon2_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image03/*.png', 10, 0.99, True))
search_icon2_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image04/*.png', 10, 0.99, True))
search_icon2_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 0, '../Images/image05/*.png', 10, 0.99, True))

select_server2_sequence = []
select_server2_sequence.append(RecognitionInfomation(
    ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer09/*.png', 1.8, 0.8, True))

action_sequence_waiting = RecognitionInfomation(
    ACTION.CLICK, RESULT.NG, END_ACTION.FOLDER_END_BREAK, 50, 4, '../Images/image_waiting/*.png', 4, 0.99, False)
action_sequence_start = RecognitionInfomation(
    ACTION.CLICK, RESULT.OK, END_ACTION.CONTINUE, 3, 0, '../Images/image_start/*.png', 1.8, 0.93, True)



action_sequence_end = RecognitionInfomation(
    ACTION.CLICK, RESULT.OK, END_ACTION.CONTINUE, 2, 2, '../Images/image_end/*.png', 1.8, 0.95, True)

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

#Imageを探してMouse pointerを移動させる
def Image_SearchAndMove(image_path,x_offset_dictionary,y_offset_dictionary,recognition_grayscale,recognition_confidence):
    try:
        x,y=pyautogui.locateCenterOnScreen(image_path,grayscale=recognition_grayscale,confidence =recognition_confidence)
        #x,y=pyautogui.locateCenterOnScreen(image_path)
        if image_path in x_offset_dictionary :
            x_offset=int(x_offset_dictionary[image_path])
            x = x + x_offset
            print( image_path+ "offset_x:" + str(x_offset))
        if image_path in y_offset_dictionary :
            y_offset=int(y_offset_dictionary[image_path])
            print( image_path+ "offset_y:" + str(y_offset))
            y = y + y_offset
        pyautogui.moveTo(x,y)
        #Logを貯めて強制終了時にFileを書き込む。
        Log_MessageAdd(message_list,"ImageSearchAndMove(" + image_path +")"+ str(x)+","+str(y))
        #毎回LogをFileni書き込む記述（遅いので没）
        #Write_Message(logfile_path , Log_MessageFormat(message))
        return True
    except:
        print("error:can not find image " + image_path)
        return False
        exit

#Mouse Action
def Action_Execute(action):
    if action == ACTION.CLICK:
        pyautogui.click()
        pyautogui.mouseUp()
    elif action == ACTION.DOUBLE_CLICK:
        pyautogui.doubleClick()
        pyautogui.mouseUp()

#条件判断回路
def Condition_Judge(condition,result):
    #条件と結果が同じならOK
    if condition == result:
        Log_MessageAdd(message_list,"Condition_Judge("+RESULT(condition).name+","+RESULT(result).name+"):OK")
        return True
    #条件がOKで結果がALL_OKならOK
    elif condition == RESULT.OK and  result == RESULT.ALL_OK:
        Log_MessageAdd(message_list,"Condition_Judge("+RESULT(condition).name+","+RESULT(result).name+"):OK(condition:ok,result:ALL_OK)")
        return True
    #それ以外はFalse
    else:
        Log_MessageAdd(message_list,"Condition_Judge("+RESULT(condition).name+","+RESULT(result).name+"):NG")
        return False

#Folder内のImageを探してMouse pointerを移動し、行動する
def Images_Action(action , end_action , end_condition , images_path , x_offset_dictionary , y_offset_dictionary , recognition_grayscale , recognition_confidence , interval_time):
    all_ok = True
    all_ng = True
    result=False
    print("Images_Action")
    for image_path in glob.glob(images_path):
        #画像検索とPointer移動
        end_result=Image_SearchAndMove(image_path,x_offset_dictionary,y_offset_dictionary,recognition_grayscale,recognition_confidence)

        
        if end_result :
            all_ng = False
            Action_Execute(action)
            time.sleep(interval_time)
            
            #条件成立での中止処理
            if end_action == END_ACTION.BREAK and  end_condition == RESULT.OK:
                Log_MessageAdd(message_list,"Images_Action:Result_OK Break(" + str(action) +")")
                return RESULT.OK
        else:
            all_ok=False
            #条件成立での中止処理
            if end_action == END_ACTION.BREAK and  end_condition == RESULT.NG:
                Log_MessageAdd(message_list,"Images_Action:Result_NG Break(" + str(action) +")")
                return RESULT.NG
        
    if all_ok == True:
        return RESULT.ALL_OK
    elif all_ng == True:
        return RESULT.NG
    else:
        return RESULT.OK

#Images_Actionを繰り返し実行する。
def Images_Action_ByInformation(recognition_information , x_offset_dictionary,y_offset_dictionary):
    all_ok = True
    all_ng = True
    end_condition = RESULT.NG
    end_condition_memory = RESULT.NG
    
    continue_flag = True
    loop01 = 0
    while continue_flag == True:
        print("loop"+str(loop01))
        #指定回数実行する。
        for loop02 in range(recognition_information.execute_number):
            Log_MessageAdd(message_list,"Execute_Number:"+str(loop02))
            end_result=Images_Action(recognition_information.action , recognition_information.end_action , recognition_information.end_condition, recognition_information.image_path ,x_offset_dictionary,y_offset_dictionary,recognition_information.recognition_grayscale,recognition_information.recognition_confidence,recognition_information.interval_time)
            if end_result != RESULT.NG:
                all_ng = False
                print("Continue:loop" + RESULT(end_result).name+"/"+str(recognition_information.execute_number))
            else:
                all_ok = False
                print("RESULT.NG:loop"+ str(loop02) +"/"+str(recognition_information.execute_number))
            #条件成立での中止処理
            if recognition_information.end_action == END_ACTION.BREAK and recognition_information.end_condition == end_result:
                Log_MessageAdd(message_list,"BREAK:retry"+str(loop01))
                break
            #条件成立での中止処理
            if recognition_information.end_action == END_ACTION.FOLDER_END_BREAK and recognition_information.end_condition == end_result:
                Log_MessageAdd(message_list,"FOLDER_END_BREAK:retry"+str(loop01))
                break
        if Condition_Judge(recognition_information.end_condition,end_result) == False and loop01 < recognition_information.retry_number:
            Log_MessageAdd(message_list,"False and retry:retry"+str(loop01))
            continue_flag = True
        else:
            Log_MessageAdd(message_list,"Break:retry"+str(loop01))
            continue_flag = False
        loop01= loop01 +1
    if all_ok == True:
        return RESULT.ALL_OK
    elif all_ng == True:
        return RESULT.NG
    else:
        return RESULT.OK

#条件が成立した時に繰り返し実行する。
def Images_ConditionCheckAndAction(name , condition  , action_recognition_information):
    action_result=RESULT.NG
    #条件を比較
    action_condition = False
    if action_recognition_information.end_condition == condition :
        action_condition = True
    elif action_recognition_information.end_condition == RESULT.ALL_OK:
        if condition==RESULT.OK:
            action_condition = True
    #条件を比較して成立したら実行
    if action_condition == True:  
        Log_MessageAdd(message_list,"Images_ConditionCheckAndAction:実行条件成立:" + name)
        action_result = Images_Action_ByInformation(action_recognition_information,x_offset_dictionary,y_offset_dictionary)
    return action_result

#強制終了時処理（Ctrl+C）
def EndProcess():
    Write_MessageList(logfile_path , message_list)
    message_list.clear()
    subprocess.Popen(["notepad",logfile_path])

#signal処理
def Signal_Handler(signal_number,frame) -> None:
    sys.exit(1)


def timecheck_ikusei():
    #放置少女育成時間チェック(イベント時にDairy消費防止12:00まで待つ)
    week_day = weekday.DayOfTheWeek(set_monday=1)
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
    return flag_execute


def timecheck_login():
    #放置少女Login時間チェック
    week_day = weekday.DayOfTheWeek(set_monday=1)   
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
    #放置少女Login時間チェック
    week_day = weekday.DayOfTheWeek(set_monday=1)   
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
           
    flag_execute = check1 or check2 
    if flag_execute:
        Log_MessageAdd(message_list,"time check" + date_time.strftime ( '%Y 年 %m 月 %d　日　(%A) %H : %M' ))

        file_path = '../Images/image_item/*.png'
        sequence_item = RecognitionInfomation(ACTION.CLICK, RESULT.OK, END_ACTION.CONTINUE, 1, 0, file_path, 0.8, 0.93, False)
        result_action = Images_Action_ByInformation(sequence_item, x_offset_dictionary, y_offset_dictionary)

        file_path = '../Images/image_highspeed/*.png'
        sequence_highspeed=RecognitionInfomation(ACTION.CLICK ,RESULT.OK, END_ACTION.CONTINUE ,1, 0 ,file_path , 0.8 , 0.93 , True)
        result_action = Images_Action_ByInformation(sequence_highspeed,x_offset_dictionary,y_offset_dictionary)

def chokyo_all():
    #放置少女調教時間チェック

    #19:40-21:45
    if datetime.time(12,30,0) <= datetime.datetime.now().time() and  datetime.datetime.now().time() <= datetime.time(13,45,0):
        check1 = True
    else:
        check1 = False
        print("check1 false")

    #19:40-21:45
    if datetime.time(19,30,0) <= datetime.datetime.now().time() and  datetime.datetime.now().time() <=  datetime.time(21,45,0):
        check2 = True 
    else:
        check2 = False
        print("check2 false")
    if check1:
        print("result check1")        
    if check2:
        print("result check2")
    if check1 or check2:
        #Sub searver周回
        print("check2")
        flag_timecheck = False
        for sequence in search_icon1_sequence:
            for server_sequence in select_server1_sequence:
                chokyo(sequence, server_sequence, flag_timecheck)
                log.Write_MessageList(logfile_path, message_list)
                message_list.clear()
        #Main searver周回
        flag_timecheck = True
        for sequence in search_icon2_sequence:
            for server_sequence in select_server2_sequence:
                chokyo(sequence, server_sequence, flag_timecheck)
                log.Write_MessageList(logfile_path, message_list)
                message_list.clear()


def chokyo(sequence, server_sequence, flag_timecheck):
    Images_Action_ByInformation(action_sequence_end, x_offset_dictionary, y_offset_dictionary)  # "終了処理", RESULT.OK
    result_file_click = Images_Action_ByInformation(sequence, x_offset_dictionary, y_offset_dictionary)  # "File選択", RESULT.OK ,
    if Condition_Judge(RESULT.OK, result_file_click):
        result_waiting = Images_Action_ByInformation(action_sequence_waiting, x_offset_dictionary, y_offset_dictionary)  # "待ち動作", result_file_click ,
        result_server = Images_Action_ByInformation(server_sequence, x_offset_dictionary, y_offset_dictionary)  # "Server選択動作", result_file_click
        result_start = Images_Action_ByInformation(action_sequence_start, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
        action_kyoudou1=RecognitionInfomation(ACTION.CLICK ,RESULT.OK, END_ACTION.CONTINUE ,3, 5 ,'../Images/image_kyoudou1/*.png' , 0.8 , 0.93 , True)
        result_action = Images_Action_ByInformation(action_kyoudou1,x_offset_dictionary,y_offset_dictionary)
        if result_action:
            action_kyoudou2=RecognitionInfomation(ACTION.CLICK ,RESULT.NG, END_ACTION.FOLDER_END_BREAK, 20,100,'../Images/image_kyoudou2/*.png' , 0.3 , 0.93 , True)
            result_action = Images_Action_ByInformation(action_kyoudou2,x_offset_dictionary,y_offset_dictionary)
        
    

def ocr_sequence():
    info_message_list=[]
    info_logfile_path='../log/log_information.txt'
    #画面Captureの文字認識
    ocr_instance = ocr.OCR()
    sequence_Infomation0 = RecognitionInfomation(
        ACTION.CLICK, RESULT.OK, END_ACTION.CONTINUE, 1, 0, '../Images/images/image_Information0/*.png', 0.8, 0.93, True)
    result_action = Images_Action_ByInformation(
        sequence_Infomation0, x_offset_dictionary, y_offset_dictionary)
    sequence_Infomation1 = RecognitionInfomation(
        ACTION.CLICK, RESULT.OK, END_ACTION.CONTINUE, 1, 0, '../Images/image_Information1/*.png', 0.8, 0.93, True)
    result_action = Images_Action_ByInformation(
        sequence_Infomation1, x_offset_dictionary, y_offset_dictionary)
    file_path = "../Images/image_information/screen_capture1.png"
    file_path2 = "../Images/image_information/screen_capture_Comment.png"
    bbox_w=700
    bbox_h=600
    bbox_x=600
    bbox_y=0
    PIL.ImageGrab.grab(bbox=(bbox_x,  bbox_y,bbox_x + bbox_w , bbox_y + bbox_h)).save(file_path)
    image = image_control.CropAndAlign_ByFilePath(file_path,
        0,
        200,
        500,
        100,
        image_control.HOLIZONTAL_ALIGN.CENTER,
        image_control.VIRTICAL_ALIGN.MIDDLE
        )
    image.save(file_path2)
    ocr_instance.Setting_BuilderText(6)
    text=ocr_instance.Recognition_ByFilePath(file_path2,"jpn")
    log.Log_MessageAdd(info_message_list,"Comment:\n"+text)

    sequence_Infomation0 = RecognitionInfomation(ACTION.CLICK, RESULT.OK, END_ACTION.CONTINUE, 1, 0, '../Images/image_Information0/*.png', 0.8, 0.93, True)
    result_action = Images_Action_ByInformation(
        sequence_Infomation0, x_offset_dictionary, y_offset_dictionary)
    sequence_Infomation2 = RecognitionInfomation(
        ACTION.CLICK, RESULT.OK, END_ACTION.CONTINUE, 1, 0, '../Images/image_Information2/*.png', 0.8, 0.93, True)
    result_action = Images_Action_ByInformation(
        sequence_Infomation2, x_offset_dictionary, y_offset_dictionary)
    if result_action:

        sequence_Infomation2=RecognitionInfomation(ACTION.CLICK ,RESULT.OK, END_ACTION.CONTINUE ,1, 0 ,'./Images/image_Information2/*.png' , 0.8 , 0.93 , True)
        result_action = Images_Action_ByInformation( sequence_Infomation2,x_offset_dictionary,y_offset_dictionary)
        file_path = "../Images/image_information/screen_capture2.png"
        file_path2 = "../Images/image_information/screen_capture_Name.png"
        file_path3 = "../Images/image_information/screen_capture_Money.png"
        file_path4 = "../Images/image_information/screen_capture_Level.png"
        bbox_w=700
        bbox_h=600
        bbox_x=600
        bbox_y=0
        PIL.ImageGrab.grab(bbox=(bbox_x,  bbox_y,bbox_x + bbox_w , bbox_y + bbox_h)).save(file_path)
        image = image_control.CropAndAlign_ByFilePath(file_path,
            100,
            45,
            140,
            70,
            image_control.HOLIZONTAL_ALIGN.LEFT,
            image_control.VIRTICAL_ALIGN.TOP
            )
        image.save(file_path2)
        image = image_control.CropAndAlign_ByFilePath(file_path,
            480,
            45,
            100,
            60,
            image_control.HOLIZONTAL_ALIGN.LEFT,
            image_control.VIRTICAL_ALIGN.TOP
            )
        image.save(file_path3)
        image = image_control.CropAndAlign_ByFilePath(file_path,
            0,
            110,
            150,
            30,
            image_control.HOLIZONTAL_ALIGN.CENTER,
            image_control.VIRTICAL_ALIGN.TOP
            )
        image.save(file_path4)
        
        ocr_instance.Setting_BuilderText(6)
        text=ocr_instance.Recognition_ByFilePath(file_path2,"jpn")
        log.Log_MessageAdd(info_message_list,"Name:"+text)
        text=ocr_instance.Recognition_ByFilePath(file_path3,"jpn")
        log.Log_MessageAdd(info_message_list,"Money:"+text)
        text=ocr_instance.Recognition_ByFilePath(file_path4,"jpn")
        log.Log_MessageAdd(info_message_list,"Level:"+text)
    Write_MessageList(info_logfile_path , info_message_list)
    info_message_list.clear()
    
    for loop1 in range(3,13):
        ocr_instance.Setting_BuilderText(loop1)
        #text=ocr_instance.Recognition(image,"jpn")
        text=ocr_instance.Recognition_ByFilePath(file_path2,"jpn")
        log.Log_MessageAdd(message_list,"ocr" + str(loop1) + ":\n" + text)
        text=ocr_instance.Recognition_ByFilePath(file_path3,"jpn")
        log.Log_MessageAdd(message_list,"ocr" + str(loop1) + ":\n" + text)
        text=ocr_instance.Recognition_ByFilePath(file_path4,"jpn")
        log.Log_MessageAdd(message_list,"ocr" + str(loop1) + ":\n" + text)

        
#Main Program実行部
def main():
    signal.signal(signal.SIGTERM, Signal_Handler)
    try:
        while 1:
            chokyo_all()
            #action_mementomori = RecognitionInfomation(ACTION.DOUBLE_CLICK, RESULT.OK, END_ACTION.CONTINUE,1, 3, '../Images/mementomori/Click00*.png', 1.8, 0.95, True)
            #result_action = Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
            #if result_action:
            #        
            #    action_mementomori = RecognitionInfomation(ACTION.DOUBLE_CLICK, RESULT.NG, END_ACTION.CONTINUE,25, 100, '../Images/mementomori/Click05*.png', 5, 0.95, True)
            #    result_action = Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
            #
            #    action_mementomori = RecognitionInfomation(ACTION.CLICK, RESULT.NG, END_ACTION.CONTINUE, 50, 3, '../Images/mementomori/Click1*.png', 1.8, 0.95, True)
            #    result_action = Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)


        log.Log_MessageAdd(message_list,"OCR start")
        ocr_sequence()
        #action_kyoudou1=RecognitionInfomation(ACTION.CLICK ,RESULT.OK, END_ACTION.CONTINUE ,10, 0 ,'../Images/image_kyoudou1/*.png' , 0.8 , 0.93 , True)
        #result_action = Images_Action_ByInformation(action_kyoudou1,x_offset_dictionary,y_offset_dictionary)
        #if result_action:
        #    action_kyoudou2=RecognitionInfomation(ACTION.CLICK ,RESULT.NG, END_ACTION.FOLDER_END_BREAK, 300,0,'../Images/image_kyoudou2/*.png' , 0.3 , 0.93 , True)
        #    result_action = Images_Action_ByInformation(action_kyoudou2,x_offset_dictionary,y_offset_dictionary)

        
        highspeed()
        log.Log_MessageAdd(message_list,"Event2 start")
        action_sequence_event2=RecognitionInfomation(ACTION.CLICK ,RESULT.OK, END_ACTION.CONTINUE ,10, 0 ,'../Images/image_event2/*.png' , 0.8 , 0.93 , True)
        result_action = Images_Action_ByInformation(action_sequence_event2,x_offset_dictionary,y_offset_dictionary)
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
