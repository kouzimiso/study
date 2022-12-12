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
import datetime

sys.path.append("../Common")
import rename
import log
import json_control

class END_ACTION(Enum):
    BREAK = 0
    FOLDER_END_BREAK = 1
    CONTINUE = 2

class RESULT(Enum):
    NG = 0
    OK = 1
    ALL_OK = 2

class ACTION(Enum):
    NONE = 0
    CLICK = 1
    DOUBLE_CLICK = 2

class DATA_TYPE(Enum):
    ENUM = 0
    NUMBER = 1
    FLOAT = 2
    STRING = 3

enum_dictionary={
    "END_ACTION.BREAK":END_ACTION.BREAK,
    "END_ACTION.FOLDER_END_BREAK":END_ACTION.FOLDER_END_BREAK,
    "END_ACTION.CONTINUE": END_ACTION.CONTINUE,
    "RESULT.NG":RESULT.NG,
    "RESULT.OK":RESULT.OK,
    "RESULT.ALL_OK": RESULT.ALL_OK,
    "ACTION.NONE":ACTION.NONE,
    "ACTION.CLICK":ACTION.CLICK,
    "ACTION.DOUBLE_CLICK":ACTION.DOUBLE_CLICK
    }

# log関係
message_list = []
logfile_path = os.path.dirname(__file__)+'/../../Log/log_auto.txt'


class RecognitionInfomation:
    def __init__(self, action, end_condition, end_action, execute_number, retry_number, image_path, interval_time, recognition_confidence, recognition_grayscale):
        self.Set_Setting(action, end_condition, end_action, execute_number, retry_number, image_path, interval_time, recognition_confidence, recognition_grayscale)
        
        print("setting_dictionary")
        print(self.setting_dictionary)
        self.setting_initial_dictionary={}

    def Set_Setting(self, action, end_condition, end_action, execute_number, retry_number, image_path, interval_time, recognition_confidence, recognition_grayscale):
        # 処理
        self.action = action
        # 終了条件
        self.end_condition = end_condition
        # 実行回数
        self.execute_number = execute_number
        # 再試行回数
        self.retry_number = retry_number
        # 終了処理
        self.end_action = end_action
        # クリックする画像を保存するフォルダ
        self.image_path = image_path
        # 画像をClickした後の待ち時間(秒)
        self.interval_time = interval_time
        # 画像認識のあいまい設定
        self.recognition_confidence = recognition_confidence
        # GrayScale設定(高速化)
        self.recognition_grayscale = recognition_grayscale
        # dictionary_setting
        self.setting_dictionary=self.Get_SettingDictionary()
        

    def Get_SettingDictionary(self):
        self.setting_dictionary={
            "action":"",
            "end_condition": self.Set_StringData(self.end_condition,DATA_TYPE.ENUM),
            "execute_number" : self.Set_StringData(self.execute_number,DATA_TYPE.NUMBER),
            "retry_number":self.Set_StringData(self.retry_number,DATA_TYPE.NUMBER),
            "end_action":self.Set_StringData(self.end_action,DATA_TYPE.ENUM),
            "image_path": self.Set_StringData(self.image_path,DATA_TYPE.STRING),
            "interval_time":self.Set_StringData(self.interval_time,DATA_TYPE.NUMBER),
            "recognition_confidence":self.Set_StringData(self.recognition_confidence,DATA_TYPE.FLOAT),
            "recognition_grayscale":self.Set_StringData(self.recognition_grayscale,DATA_TYPE.FLOAT)
            }
        return self.setting_dictionary

    def Set_SettingDictionary(self,input_dictionary):
        self.setting_dictionary=input_dictionary
        
        self.end_condition= self.Get_Data("end_condition",DATA_TYPE.ENUM)
        self.execute_number= self.Get_Data("execute_number",DATA_TYPE.NUMBER)
        self.retry_number= self.Get_Data("retry_number",DATA_TYPE.NUMBER)
        self.end_action=self.Get_Data("end_action",DATA_TYPE.ENUM)
        self.image_path=self.Get_Data("image_path",DATA_TYPE.STRING)
        self.interval_time=self.Get_Data("interval_time",DATA_TYPE.NUMBER)
        self.recognition_confidence=self.Get_Data("recognition_confidence",DATA_TYPE.FLOAT)
        self.recognition_grayscale=self.Get_Data("recognition_grayscale",DATA_TYPE.FLOAT)
    
    def Get_Data(self,data_name,data_type=DATA_TYPE.ENUM):
        if data_type == DATA_TYPE.ENUM:
            print("data_name:"+data_name)#"end_condition"のような文字Data
            parameter_name = self.setting_dictionary[data_name]
            print("parameter_name:"+parameter_name)
            return enum_dictionary[parameter_name]
        elif data_type == DATA_TYPE.NUMBER:
            return int(self.setting_dictionary[data_name])
        elif data_type == DATA_TYPE.FLOAT:
            return float(self.setting_dictionary[data_name])
        elif data_type == DATA_TYPE.STRING:
            return str(self.setting_dictionary[data_name])            
        else:
            return str(self.setting_dictionary[data_name])

    def Set_StringData(self,data,data_type=DATA_TYPE.ENUM):
        if data_type == DATA_TYPE.ENUM:
            return data.name
            #return END_ACTION(data).name
        elif data_type == DATA_TYPE.NUMBER:
            return str(data)
        elif data_type == DATA_TYPE.FLOAT:
            return str(data)
        elif data_type == DATA_TYPE.STRING:
            return  str(data)            
        else:
            return  str(data) 

def Image_SearchAndXY(image_path, recognition_grayscale, recognition_confidence):
    result = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)
    x, y = result
    return x, y

# Imageを探してMouse pointerを移動させる
def Image_SearchAndMove(image_path, x_offset_dictionary, y_offset_dictionary, recognition_grayscale, recognition_confidence):
    try:
        result = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)
        if result is not None:
            x,y=result
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
            log.Log_MessageAdd(message_list, "ImageSearchAndMove(" + image_path + ")" + str(x)+","+str(y))
            # 毎回LogをFileni書き込む記述（遅いので没）
            #Write_Message(logfile_path , Log_MessageFormat(message))
            return True
        else:
            import traceback
            traceback.print_exc()
            print("error:can not find image on screen " + image_path)
            return False
    except:
        import traceback
        traceback.print_exc()
        log.Log_MessageAdd(message_list, "unexplained error:ImageSearchAndMove(" + image_path + ")")
        print("x_offset_dictionary")
        print(x_offset_dictionary)
        print("y_offset_dictionary")
        print(y_offset_dictionary)
        print("recognition_grayscale")
        print(recognition_grayscale)
        print("recognition_confidence")
        print(recognition_confidence)

        return False
        exit

# Mouse Action
def Action_Execute(action):
    if action == ACTION.CLICK:
        pyautogui.click()
        pyautogui.mouseUp()
    elif action == ACTION.DOUBLE_CLICK:
        pyautogui.doubleClick()
        pyautogui.mouseUp()

# 条件判断回路
def Condition_Judge(condition, result):
    # 条件と結果が同じならOK
    if condition == result:
        log.Log_MessageAdd(message_list, "Condition_Judge(" + RESULT(condition).name+","+RESULT(result).name+"):OK")
        return True
    # 条件がOKで結果がALL_OKならOK
    elif condition == RESULT.OK and result == RESULT.ALL_OK:
        log.Log_MessageAdd(message_list, "Condition_Judge("+RESULT(condition).name + ","+RESULT(result).name+"):OK(condition:ok,result:ALL_OK)")
        return True
    # それ以外はFalse
    else:
        log.Log_MessageAdd(message_list, "Condition_Judge(" + RESULT(condition).name + ","+RESULT(result).name+"):NG")
        return False

Images_Action_Result = {}
def Images_Action_ResultInit(dictionary , detect = 0 , undetect = 0 , total_detect = 0 , total_undetect = 0):
    for dictionary_key in dictionary.keys():
        dictionary[dictionary_key]["detect"]  = detect
        dictionary[dictionary_key]["undetect"] = undetect
        #print("Images_Action_ResultInit:"+dictionary_key)
        if dictionary_key not in dictionary:
            dictionary[dictionary_key]["total_detect"] = total_detect
            dictionary[dictionary_key]["total_undetect"] = total_undetect
    #print(dictionary)
    return dictionary


def rate(value,*args):
    total=value+sum(args)
    if 0 != total:
        return float(value)/float(total)
    else:
        return 0 
    
def Images_Action_ResultSet(dictionary,dictionary_key,detect,undetect):
    if dictionary_key in dictionary:
        dictionary[dictionary_key]["detect"]  += detect
        dictionary[dictionary_key]["undetect"] += undetect
        dictionary[dictionary_key]["total_detect"]  += detect
        dictionary[dictionary_key]["total_undetect"] += undetect
        
        dictionary[dictionary_key]["detect_rate"] = rate(dictionary[dictionary_key]["detect"] , dictionary[dictionary_key]["undetect"])        
        
        dictionary[dictionary_key]["total_detect_rate"] = rate(dictionary[dictionary_key]["total_detect"] , dictionary[dictionary_key]["total_undetect"])
        dictionary[dictionary_key]["date"] = datetime.datetime.now().strftime ( '%Y/%m/%d(%A) %H:%M' )
    else:
        dictionary[dictionary_key] = {
            "detect" : detect,
            "undetect" : undetect,
            "detect_rate" : rate(detect,undetect),            
            "total_detect" :detect,
            "total_undetect" : undetect,
            "total_detect_rate" :  rate(detect,undetect)   
        }
    return dictionary

def InfomationToString():
    global Images_Action_Result
    if Images_Action_Result is None:
        return ""
    else:
        return str(Images_Action_Result).encode().decode("unicode-escape")
        #return str(Images_Action_Result).encode().decode("string-escape")
    
def WriteInfomationToJson(file_path):
    global Images_Action_Result    
    json_control.WriteDictionary(file_path,Images_Action_Result)

def ReadInfomationFromJson(file_path):
    global Images_Action_Result
    try:
        Images_Action_Result = json_control.ReadDictionary(file_path,Images_Action_Result)
    except:
        Images_Action_Result={}
        log.Log_MessageAdd(message_list, "[ERROR]ReadInfomationFromJson:Json Read Error")
    return Images_Action_Result

# Folder内のImageを探してMouse pointerを移動し、行動する
def Images_Action(action, end_action, end_condition, images_path, x_offset_dictionary, y_offset_dictionary, recognition_grayscale, recognition_confidence, interval_time):
    all_ok = True
    all_ng = True
    result = False
    global Images_Action_Result

    for image_path in glob.glob(images_path):
        # 画像検索とPointer移動
        end_result = Image_SearchAndMove(image_path, x_offset_dictionary, y_offset_dictionary, recognition_grayscale, recognition_confidence)
        if end_result:
            Images_Action_Result=Images_Action_ResultSet(Images_Action_Result,image_path,1,0)        
            Images_Action_Result=Images_Action_ResultSet(Images_Action_Result,"all_image",1,0)        
            all_ng = False
            Action_Execute(action)
            time.sleep(interval_time)

            # 条件成立での中止処理
            if end_action == END_ACTION.BREAK and end_condition == RESULT.OK:
                log.Log_MessageAdd(message_list, "Images_Action:Result_OK Break(" + str(action) + ")")
                return RESULT.OK
        else:
            Images_Action_Result=Images_Action_ResultSet(Images_Action_Result,image_path,0,1)        
            Images_Action_Result=Images_Action_ResultSet(Images_Action_Result,"all_image",0,1)        
            all_ok = False
            # 条件成立での中止処理
            if end_action == END_ACTION.BREAK and end_condition == RESULT.NG:
                log.Log_MessageAdd(message_list, "Images_Action:Result_NG Break(" + str(action) + ")")
                return RESULT.NG
    if all_ok == True:
        return RESULT.ALL_OK
    elif all_ng == True:
        return RESULT.NG
    else:
        return RESULT.OK

# Images_Actionを繰り返し実行する。
def Images_Action_ByInformation(recognition_information, x_offset_dictionary, y_offset_dictionary):
    all_ok = True
    all_ng = True
    end_condition = RESULT.NG
    end_condition_memory = RESULT.NG

    continue_flag = True
    loop01 = 0

    while continue_flag == True:
        print("loop"+str(loop01))
        # 指定回数実行する。
        for loop02 in range(recognition_information.execute_number):
            log.Log_MessageAdd(message_list, "Execute_Number:"+str(loop02))
            end_result = Images_Action(recognition_information.action, recognition_information.end_action, recognition_information.end_condition, recognition_information.image_path,x_offset_dictionary, y_offset_dictionary, recognition_information.recognition_grayscale, recognition_information.recognition_confidence, recognition_information.interval_time)
            if end_result != RESULT.NG:
                all_ng = False
                print("Continue:loop" + RESULT(end_result).name + "/"+str(recognition_information.execute_number))
            else:
                all_ok = False
                print("RESULT.NG:loop" + str(loop02) + "/" + str(recognition_information.execute_number))
            # 条件成立での中止処理
            if recognition_information.end_action == END_ACTION.BREAK and recognition_information.end_condition == end_result:
                log.Log_MessageAdd(message_list, "BREAK:retry"+str(loop01))
                break
            # 条件成立での中止処理
            if recognition_information.end_action == END_ACTION.FOLDER_END_BREAK and recognition_information.end_condition == end_result:
                log.Log_MessageAdd(message_list, "FOLDER_END_BREAK:retry"+str(loop01))
                break
        if Condition_Judge(recognition_information.end_condition, end_result) == False and loop01 < recognition_information.retry_number:
            log.Log_MessageAdd(message_list, "False and retry:retry"+str(loop01))
            continue_flag = True
        else:
            log.Log_MessageAdd(message_list, "EndResult:retry"+str(loop01))
            continue_flag = False
        loop01 = loop01 + 1
    log.Write_MessageList(logfile_path, message_list)
    message_list.clear()
    if all_ok == True:
        return RESULT.ALL_OK
    elif all_ng == True:
        return RESULT.NG
    else:
        return RESULT.OK

# 条件が成立した時に繰り返し実行する。
def Images_ConditionCheckAndAction(name, condition, action_recognition_information, x_offset_dictionary, y_offset_dictionary):
    action_result = RESULT.NG
    # 条件を比較
    action_condition = False
    if action_recognition_information.end_condition == condition:
        action_condition = True
    elif action_recognition_information.end_condition == RESULT.ALL_OK:
        if condition == RESULT.OK:
            action_condition = True
    # 条件を比較して成立したら実行
    if action_condition == True:
        log.Log_MessageAdd(message_list, "Images_ConditionCheckAndAction:実行条件成立:" + name)
        action_result = Images_Action_ByInformation(action_recognition_information, x_offset_dictionary, y_offset_dictionary)
    return action_result


def Image_AroundMouse(file_path, flag_overwrite=True, wide=0, height=0, dupplicate_format="{}({:0=3}){}"):
    x, y = pyautogui.position()

    Image_AroundPoint(file_path, flag_overwrite, x, y, wide, height, dupplicate_format)


def Image_AroundPoint(file_path, flag_overwrite=True, x=0, y=0, wide=0, height=0, dupplicate_format="{}({:0=3}){}"):
    if flag_overwrite == False:
        path = rename.duplicate_rename(file_path, dupplicate_format)
    else:
        path = file_path
    if wide == 0 or height == 0:
        PIL.ImageGrab.grab().save(path)
    else:
        bbox_w = wide
        bbox_h = height
        bbox_x = max(0, x - bbox_w/2)
        bbox_y = max(0, y - bbox_h/2)
        PIL.ImageGrab.grab(bbox=(bbox_x,  bbox_y, bbox_x +
                           bbox_w, bbox_y + bbox_h)).save(path)
