## $python 画像自動Click ##
# 設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import time
import datetime
import sys
import os
import pyautogui
import cv2
import glob
import signal
import subprocess
import PIL

sys.path.append("./Common")
sys.path.append("./Models")
sys.path.append("./ViewModels")
sys.path.append("./Views")
import image_control
import log
import weekday
import ocr
import auto


# log関係
message_list = []
logfile_path = '../Log/log.txt'

print("Images_Action_ResultInit 起動前")
auto.Images_Action_Result=auto.ReadInfomationFromJson("../Log/houchi.json")
auto.Images_Action_Result=auto.Images_Action_ResultInit(auto.Images_Action_Result)

# 画像認識動作設定
search_icon1_sequence = []
search_icon1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image00/*.png', 10, 0.99, True))
search_icon1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image01/*.png', 10, 0.97, True))

select_server1_sequence = []
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer01/*.png', 1.8, 0.8, True))
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer02/*.png', 1.8, 0.8, True))
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer03/*.png', 1.8, 0.8, True))
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer04/*.png', 1.8, 0.8, True))
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer05/*.png', 1.8, 0.8, True))
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer06/*.png', 1.8, 0.8, True))
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer07/*.png', 1.8, 0.8, True))
select_server1_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer08/*.png', 1.8, 0.8, True))


search_icon2_sequence = []
search_icon2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image00/*.png', 10, 0.99, True))
search_icon2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image01/*.png', 10, 0.97, True))
search_icon2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image02/*.png', 10, 0.99, True))
search_icon2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image03/*.png', 10, 0.99, True))
search_icon2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image04/*.png', 10, 0.99, True))
search_icon2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image05/*.png', 10, 0.99, True))
search_icon2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 0, '../Images/image06/*.png', 10, 0.99, True))

select_server2_sequence = []
select_server2_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK, 2, 5, '../Images/image_SelectServer09/*.png', 1.8, 0.8, True))


action_sequence_waiting = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.NG, auto.END_ACTION.CONTINUE, 3, 20, '../Images/image_waiting/*.png', 4, 0.99, False)
action_sequence_start = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 2, 0, '../Images/image_start/Click0*.png', 1.8, 0.93, True)
action_sequence_start2 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_start/*.png', 1.8, 0.93, True)
action_sequence_main = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 4, 0, '../Images/image/*.png', 0.5, 0.93, True)
action_sequence_main2 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.NG, auto.END_ACTION.CONTINUE, 3, 100, '../Images/image/Click02*.png', 0.5, 0.93, True)
action_sequence_event = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 3, 0, '../Images/image_event/*.png', 0.5, 0.93, True)
action_sequence_event2 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 2, 2, '../Images/image_event2/*.png', 0.8, 0.93, True)
action_sequence_ikusei = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 3, 1, '../Images/image_ikusei/*.png', 1.8, 0.93, True)
action_sequence_end = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 2, 2, '../Images/image_end/*.png', 1.8, 0.95, True)
action_sequence_shutdown = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.ALL_OK, auto.END_ACTION.CONTINUE, 2, 2, '../Images/image_shutdown/*.png', 5, 0.95, True)


# アニメーションするボタンが押せない対策
# 画像を探してずらした位置をクリックする設定。{画像Path:ずらす位置}の形式で記述する。
x_offset_dictionary = {'../Images/image_ikusei\Click9254.png': "0"}
y_offset_dictionary = {'../Images/image_ikusei\Click9254.png': "-60", '../Images/image_ikusei\Click2003.png': "-30", '../Images/image_ikusei\Click9204.png': "-60",
                       '../Images/image_event2\Click9254.png': "-60", '../Images/image_event2\Click2003.png': "-30", '../Images/image_event2\Click9204.png': "-60"}

# Imageを探してMouse pointerを移動させる


def Image_SearchAndMove(image_path, x_offset_dictionary, y_offset_dictionary, recognition_grayscale, recognition_confidence):
    try:
        x, y = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)
        # x,y=pyautogui.locateCenterOnScreen(image_path)
        if image_path in x_offset_dictionary:
            x_offset = int(x_offset_dictionary[image_path])
            x = x + x_offset
            print(image_path + "offset_x:" + str(x_offset))
        if image_path in y_offset_dictionary:
            y_offset = int(y_offset_dictionary[image_path])
            print(image_path + "offset_y:" + str(y_offset))
            y = y + y_offset
        pyautogui.moveTo(x, y)
        # Logを貯めて強制終了時にFileを書き込む。
        log.Log_MessageAdd(message_list, "ImageSearchAndMove("+image_path + ")" + str(x)+","+str(y))
        # 毎回LogをFileni書き込む記述（遅いので没）
        #log.Write_Message(logfile_path , Log_MessageFormat(message))
        return True
    except:
        print("error:can not find image " + image_path)
        return False
        exit


# 強制終了時処理（Ctrl+C）
def EndProcess():
    log.Write_MessageList(logfile_path, message_list)
    message_list.clear()
    subprocess.Popen(["notepad", logfile_path])

# signal処理
def Signal_Handler(signal_number, frame) -> None:
    sys.exit(1)


def timecheck_ikusei():
    # 放置少女育成時間チェック(イベント時にDairy消費防止12:00まで待つ)
    week_day = weekday.DayOfTheWeek(set_monday=1)
    date_time = datetime.datetime.now()
    #time1 = datetime.time(12,00,00)
    time1 = datetime.time(8, 00, 00)
    time2 = datetime.time(23, 45, 00)

    day_of_weekday1 = week_day.SaturDay
    day_of_weekday2 = week_day.SunDay
    check1 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check1:
        message_list.extend(week_day.message_list)

    day_of_weekday1 = week_day.MonDay
    day_of_weekday2 = week_day.MonDay
    week_day.message_list.clear()
    check2 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check2:
        message_list.extend(week_day.message_list)

    day_of_weekday1 = week_day.TuesDay
    day_of_weekday2 = week_day.ThursDay
    week_day.message_list.clear()
    check3 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check3:
        message_list.extend(week_day.message_list)

    day_of_weekday1 = week_day.FriDay
    day_of_weekday2 = week_day.FriDay
    week_day.message_list.clear()
    check4 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check4:
        message_list.extend(week_day.message_list)

    flag_execute = check1 or check2 or check3 or check4
    if flag_execute:
        log.Log_MessageAdd(message_list, "time check" + date_time.strftime('%Y 年 %m 月 %d　日　(%A) %H : %M'))
    return flag_execute


def timecheck_login():
    # 放置少女Login時間チェック
    week_day = weekday.DayOfTheWeek(set_monday=1)
    date_time = datetime.datetime.now()

    time1 = datetime.time(8, 00, 00)
    time2 = datetime.time(23, 45, 00)

    day_of_weekday1 = week_day.SaturDay
    day_of_weekday2 = week_day.SunDay
    check1 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check1:
        message_list.extend(week_day.message_list)

    day_of_weekday1 = week_day.MonDay
    day_of_weekday2 = week_day.MonDay
    week_day.message_list.clear()
    check2 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check2:
        message_list.extend(week_day.message_list)

    day_of_weekday1 = week_day.TuesDay
    day_of_weekday2 = week_day.ThursDay
    week_day.message_list.clear()
    check3 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check3:
        message_list.extend(week_day.message_list)

    day_of_weekday1 = week_day.FriDay
    day_of_weekday2 = week_day.FriDay
    week_day.message_list.clear()
    check4 = week_day.Check_WithinRangeDay(date_time, time1, day_of_weekday1, time2, day_of_weekday2)
    if check4:
        message_list.extend(week_day.message_list)

    flag_execute = check1 or check2 or check3 or check4
    if flag_execute:
        log.Log_MessageAdd(message_list, "time check" + date_time.strftime('%Y 年 %m 月 %d　日　(%A) %H : %M'))
    return flag_execute


def timecheck_afternoon():
    # 12:30-13:45
    if datetime.time(12, 30, 0) <= datetime.datetime.now().time() and datetime.datetime.now().time() <= datetime.time(13, 45, 0):
        return True #通常時
    else:
        return False


def timecheck_evening():
    # 19:40-22:45
    if datetime.time(19, 40, 0) <= datetime.datetime.now().time() and datetime.datetime.now().time() <= datetime.time(22, 45, 0):
        return True 
    else:
        return False


def information_check():
    info_message_list = []
    info_logfile_path = '../Log/log_information.txt'
    # 画面Captureの文字認識
    ocr_instance = ocr.OCR()

    sequence_Infomation0 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 1, 0, '../Images/images/image_Information0/*.png', 0.8, 0.93, True)
    result_action = auto.Images_Action_ByInformation(sequence_Infomation0, x_offset_dictionary, y_offset_dictionary)
    sequence_Infomation1 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_Information1/*.png', 0.8, 0.93, True)
    result_action = auto.Images_Action_ByInformation(sequence_Infomation1, x_offset_dictionary, y_offset_dictionary)
    if result_action:
        file_path = "../Images/image_information/screen_capture1.png"
        file_path2 = "../Images/image_information/screen_capture_Comment.png"
        bbox_w = 700
        bbox_h = 600
        bbox_x = 600
        bbox_y = 0
        PIL.ImageGrab.grab(bbox=(bbox_x,  bbox_y, bbox_x +
                           bbox_w, bbox_y + bbox_h)).save(file_path)
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
        text = ocr_instance.Recognition_ByFilePath(file_path2, "jpn")
        log.Log_MessageAdd(info_message_list, "Comment:\n"+text)
    sequence_Infomation0 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_Information0/*.png', 0.8, 0.93, True)
    result_action = auto.Images_Action_ByInformation(sequence_Infomation0, x_offset_dictionary, y_offset_dictionary)
    sequence_Infomation2 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 1, 0, '../Images/image_Information2/*.png', 0.8, 0.93, True)
    result_action = auto.Images_Action_ByInformation(sequence_Infomation2, x_offset_dictionary, y_offset_dictionary)
    if result_action:

        file_path = "../Images/image_information/screen_capture2.png"
        file_path2 = "../Images/image_information/screen_capture_Name.png"
        file_path3 = "../Images/image_information/screen_capture_Money.png"
        file_path4 = "../Images/image_information/screen_capture_Level.png"
        bbox_w = 700
        bbox_h = 600
        bbox_x = 600
        bbox_y = 0
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
        text = ocr_instance.Recognition_ByFilePath(file_path2, "jpn")
        log.Log_MessageAdd(info_message_list, "Name:"+text)
        text = ocr_instance.Recognition_ByFilePath(file_path3, "jpn")
        log.Log_MessageAdd(info_message_list, "Money:"+text)
        text = ocr_instance.Recognition_ByFilePath(file_path4, "jpn")
        log.Log_MessageAdd(info_message_list, "Level:"+text)
        log.Write_MessageList(info_logfile_path, info_message_list)
    info_message_list.clear()
    
def highspeed():
    #放置少女2.5倍日 特殊動作
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
        log.Log_MessageAdd(message_list,"time check" + date_time.strftime ( '%Y 年 %m 月 %d　日　(%A) %H : %M' ))

        file_path = '../Images/image_item/*.png'
        sequence_item = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 1, 0, file_path, 0.8, 0.93, False)
        result_action = auto.Images_Action_ByInformation(sequence_item, x_offset_dictionary, y_offset_dictionary)

        file_path = '../Images/image_highspeed/*.png'
        sequence_highspeed=auto.RecognitionInfomation(auto.ACTION.CLICK ,auto.RESULT.OK, auto.END_ACTION.CONTINUE ,1, 0 ,file_path , 0.8 , 0.93 , True)
        result_action = auto.Images_Action_ByInformation(sequence_highspeed,x_offset_dictionary,y_offset_dictionary)

        file_path = '../Images/image_item/*.png'
        sequence_item = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 1, 0, file_path, 0.8, 0.93, False)
        result_action = auto.Images_Action_ByInformation(sequence_item, x_offset_dictionary, y_offset_dictionary)
        
        result_start = auto.Images_Action_ByInformation(action_sequence_start, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting

def chokyo_time_check():
    #放置少女調教時間チェック
    #12:35-13:45
    if datetime.time(12,35,0) <= datetime.datetime.now().time() and  datetime.datetime.now().time() <= datetime.time(13,45,0):
        check1 = True
    else:
        check1 = False
        print("check1 false")
    #19:40-20:45
    if datetime.time(19,45,0) <= datetime.datetime.now().time() and  datetime.datetime.now().time() <=  datetime.time(20,45,0):
        check2 = True 
    else:
        check2 = False
        print("check2 false")
    if check1:
        print("result check1")        
    if check2:
        print("result check2")
    if check1 or check2:
        return True
    else:
        return False

def chokyo_all():
    while chokyo_time_check():
        #Sub searver周回
        print("check2")
        flag_timecheck = False
        for sequence in search_icon1_sequence:
            for server_sequence in select_server1_sequence:
                if chokyo_time_check():
                    chokyo(sequence, server_sequence, flag_timecheck)
                    log.Write_MessageList(logfile_path, message_list)
                    message_list.clear()
        #Main searver周回
        flag_timecheck = True
        for sequence in search_icon2_sequence:
            for server_sequence in select_server2_sequence:
                if chokyo_time_check():
                    chokyo(sequence, server_sequence, flag_timecheck)
                    log.Write_MessageList(logfile_path, message_list)
                    message_list.clear()
                
def chokyo(sequence, server_sequence, flag_timecheck):
    auto.Images_Action_ByInformation(action_sequence_end, x_offset_dictionary, y_offset_dictionary)  # "終了処理", auto.RESULT.OK
    result_file_click = auto.Images_Action_ByInformation(sequence, x_offset_dictionary, y_offset_dictionary)  # "File選択", auto.RESULT.OK ,
    if auto.Condition_Judge(auto.RESULT.OK, result_file_click):
        result_waiting = auto.Images_Action_ByInformation(action_sequence_waiting, x_offset_dictionary, y_offset_dictionary)  # "待ち動作", result_file_click ,
        result_server = auto.Images_Action_ByInformation(server_sequence, x_offset_dictionary, y_offset_dictionary)  # "Server選択動作", result_file_click
        result_start = auto.Images_Action_ByInformation(action_sequence_start, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
        action_kyoudou1=auto.RecognitionInfomation(auto.ACTION.CLICK ,auto.RESULT.OK, auto.END_ACTION.CONTINUE ,3, 2 ,'../Images/image_kyoudou1/*.png' , 0.8 , 0.93 , True)
        result_action = auto.Images_Action_ByInformation(action_kyoudou1,x_offset_dictionary,y_offset_dictionary)
        if auto.Condition_Judge(auto.RESULT.OK, result_action):
            action_kyoudou2=auto.RecognitionInfomation(auto.ACTION.CLICK ,auto.RESULT.NG, auto.END_ACTION.FOLDER_END_BREAK, 5,2,'../Images/image_kyoudou2/*.png' , 0.3 , 0.93 , True)
            result_action = auto.Images_Action_ByInformation(action_kyoudou2,x_offset_dictionary,y_offset_dictionary)

def event2( flag_timecheck):
    if flag_timecheck and datetime.time(00,00,0) <= datetime.datetime.now().time() and  datetime.datetime.now().time() <= datetime.time(20,00,0):       
        action_sequence_event3 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 6, 0, '../Images/image_event2/Click9*.png', 0.8, 0.93, True)
        result_action = auto.Images_Action_ByInformation(action_sequence_event3, x_offset_dictionary, y_offset_dictionary)
    else:
        result_action = auto.Images_Action_ByInformation(action_sequence_event2, x_offset_dictionary, y_offset_dictionary)

def UnderWare():
    for i in range(2):
        action_underware = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE,3, 0, '../Images/UnderWare/Click00*.png', 0, 0.93, True)
        result_action = auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
        for i in range(10):
            action_underware = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE ,2, 2, '../Images/UnderWare/Click010*.png', 0, 0.93, True)
            result_action = auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            action_underware = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.BREAK ,3, 2, '../Images/UnderWare/Click011*.png', 0, 0.97, True)
            result_action = auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            #action_underware = RecognitionInfomation(ACTION.CLICK, RESULT.OK, END_ACTION.BREAK ,1, 20, '../Images/UnderWare/Click012*.png', 0, 0.85, True)
            #result_action = Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            #action_underware = RecognitionInfomation(ACTION.CLICK, RESULT.OK, END_ACTION.BREAK ,1, 20, '../Images/UnderWare/Click013*.png', 0, 0.85, True)
            #result_action = Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            action_underware = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.ALL_OK, auto.END_ACTION.FOLDER_END_BREAK ,1, 0, '../Images/UnderWare/Click014*.png', 0, 0.93, True)
            result_action = auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
        action_underware = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE, 7, 2, '../Images/UnderWare/Click02*.png', 0, 0.93, True)
        result_action = auto.Images_Action_ByInformation(action_underware,x_offset_dictionary,y_offset_dictionary)
            
def main_process(sequence, server_sequence, flag_timecheck):
    auto.Images_Action_ByInformation(action_sequence_end, x_offset_dictionary, y_offset_dictionary)  # "終了処理", auto.RESULT.OK
    if flag_timecheck == False:
        flag_login = True
        flag_execute = timecheck_ikusei()
        #flag_execute = True   #Event時 自動回し優先
    elif timecheck_afternoon():
        flag_login = False   #通常時
        flag_execute = False
        #flag_login = True    #Event時 自動回し優先
        #flag_execute = True
        log.Log_MessageAdd(message_list, "time_check：正午")
    elif timecheck_evening():
        flag_login = False   #通常時
        flag_execute = False
        #flag_login = True    #Event時 自動回し優先
        #flag_execute = True
        log.Log_MessageAdd(message_list, "time_check：夜")
    else:
        flag_login = timecheck_login()
        flag_execute = timecheck_ikusei()

    if flag_login or flag_execute:
        result_file_click = auto.Images_Action_ByInformation(sequence, x_offset_dictionary, y_offset_dictionary)  # "File選択", auto.RESULT.OK ,
    else:
        result_file_click = auto.RESULT.NG
    
    if auto.Condition_Judge(auto.RESULT.OK, result_file_click):
        result_waiting = auto.Images_Action_ByInformation(action_sequence_waiting, x_offset_dictionary, y_offset_dictionary)  # "待ち動作", result_file_click ,
        result_server = auto.Images_Action_ByInformation(server_sequence, x_offset_dictionary, y_offset_dictionary)  # "Server選択動作", result_file_click
 
        if auto.Condition_Judge(auto.RESULT.OK, result_server):
            if flag_login or flag_execute:
                result_start = auto.Images_Action_ByInformation(action_sequence_start, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
                result_start = auto.Images_Action_ByInformation(action_sequence_start2, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
                information_check()
                event2(flag_timecheck)
            if flag_login:
                log.Log_MessageAdd(message_list, "time_check:無料ポチポチ実行")
                result_action = auto.Images_Action_ByInformation(action_sequence_main, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
                action_sequence_main3 = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.NG, auto.END_ACTION.CONTINUE, 3, 5, '../Images/image/Click07*.png', 0.2, 0.93, True)
                result_action = auto.Images_Action_ByInformation(action_sequence_main3, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
                result_action = auto.Images_Action_ByInformation(action_sequence_main2, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
                result_action = auto.Images_Action_ByInformation(action_sequence_event, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
            if flag_execute:
                log.Log_MessageAdd(message_list, "time_check:育成実行")
                result_action = auto.Images_Action_ByInformation(action_sequence_ikusei, x_offset_dictionary, y_offset_dictionary)  # "プロセス実行", result_waiting
                
            if flag_login or flag_execute:
                #action_kyoudou1=auto.RecognitionInfomation(auto.ACTION.CLICK ,auto.RESULT.OK, auto.END_ACTION.CONTINUE ,10, 0 ,'../Images/image_kyoudou1/*.png' , 0.8 , 0.93 , True)
                #result_action = auto.Images_Action_ByInformation(action_kyoudou1,x_offset_dictionary,y_offset_dictionary)
                #if result_action:
                #    action_kyoudou2=auto.RecognitionInfomation(auto.ACTION.CLICK ,auto.RESULT.NG, auto.END_ACTION.FOLDER_END_BREAK, 3,4,'../Images/image_kyoudou2/*.png' , 0.3 , 0.93 , True)
                #    result_action = auto.Images_Action_ByInformation(action_kyoudou2,x_offset_dictionary,y_offset_dictionary)
                event2(flag_timecheck)
            highspeed()
            UnderWare()
        #調教割り込み
        chokyo_all()

# Main Program実行部
def main():
    signal.signal(signal.SIGTERM, Signal_Handler)
    try:
        while 1:
            #Hospot起動
            action_hotspot = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.OK, auto.END_ACTION.FOLDER_END_BREAK, 2, 2, '../Images/hotspot/*.png', 1.8, 0.95, True)
            result_action = auto.Images_Action_ByInformation(action_hotspot,x_offset_dictionary,y_offset_dictionary)
            
            #終了処理
            auto.Images_Action_ByInformation(action_sequence_end, x_offset_dictionary, y_offset_dictionary)  # "終了処理", auto.RESULT.OK
            
            #調教割り込み
            chokyo_all()
                        
            #mementomori実行
            action_mementomori = auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.OK, auto.END_ACTION.CONTINUE,1, 3, '../Images/mementomori/Click00*.png', 1.8, 0.95, True)
            result_action = auto.Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
            if auto.Condition_Judge(auto.RESULT.OK, result_action):
                action_mementomori = auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK, auto.RESULT.NG, auto.END_ACTION.CONTINUE,25, 100, '../Images/mementomori/Click05*.png', 5, 0.95, True)
                result_action = auto.Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
                
                action_mementomori = auto.RecognitionInfomation(auto.ACTION.CLICK, auto.RESULT.NG, auto.END_ACTION.CONTINUE, 3, 5, '../Images/mementomori/Click1*.png', 1.8, 0.95, True)
                result_action = auto.Images_Action_ByInformation(action_mementomori,x_offset_dictionary,y_offset_dictionary)
                auto.WriteInfomationToJson("../Log/mementomori.json")    
            #Sub searver周回
            flag_timecheck = False
            for sequence in search_icon1_sequence:
                for server_sequence in select_server1_sequence:
                    main_process(sequence, server_sequence, flag_timecheck)
                    log.Write_MessageList(logfile_path, message_list)
                    message_list.clear()
                    auto.WriteInfomationToJson("../Log/houchi.json")    
            #Main searver周回
            flag_timecheck = True
            for sequence in search_icon2_sequence:
                for server_sequence in select_server2_sequence:
                    main_process(sequence, server_sequence, flag_timecheck)
                    log.Write_MessageList(logfile_path, message_list)
                    message_list.clear()
                    auto.WriteInfomationToJson("../Log/houchi.json")    

            auto.Images_Action_ByInformation(action_sequence_end, x_offset_dictionary, y_offset_dictionary)  # "終了処理", auto.RESULT.OK
            #auto.Images_Action_ByInformation( action_sequence_shutdown,x_offset_dictionary,y_offset_dictionary)#"Shutdown処理", auto.RESULT.ALL_OK#
            os.system('shutdown -r -f')
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        EndProcess()
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    sys.exit(main())
