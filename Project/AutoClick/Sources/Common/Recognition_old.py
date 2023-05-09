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
import datetime
import dataclasses
import inspect

sys.path.append("../Common")
sys.path.append("../../Common")
import Rename
import Log
import JSON_Control
import Auto

# log関係
message_list = []
logfile_path = os.path.dirname(__file__)+'/../../Log/log_auto.txt'

@dataclasses.dataclass
class RecognitionInfomation:
    action : Auto.ACTION 
    end_condition : Auto.RESULT 
    end_action : Auto.END_ACTION
    execute_number : int =0
    retry_number : int =0 
    image_path : str = ""
    interval_time : float = 0.1
    recognition_confidence : float = 1.0
    recognition_grayscale : float = 0
    x_offset_dictionary : dict = None
    y_offset_dictionary : dict = None
    def __init__(
        self,
        action = Auto.ACTION.NONE , 
        end_condition = Auto.RESULT.OK , 
        end_action = Auto.END_ACTION.CONTINUE,
        execute_number = 0,
        retry_number = 0 , 
        image_path = "",
        interval_time = 0.1,
        recognition_confidence =1.0 , 
        recognition_grayscale = 0
        ):
        self.Set_Setting(action , end_condition , end_action , execute_number , retry_number , image_path , interval_time , recognition_confidence , recognition_grayscale)
        
        self.setting_initial_dictionary={}

    def Set_Setting(self , action , end_condition , end_action , execute_number , retry_number , image_path, interval_time, recognition_confidence, recognition_grayscale):
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

#Dictionaryで設定したい時と個別設定値で設定したい場合がある。
class Recognition:
    setting:RecognitionInfomation
    #setting_dictionary : dict={}

    def __init__(self, input_dictionary = {}):
        #self.setting=RecognitionInfomation(**input_dictionary)
        self.logger = Log.Logs(input_dictionary)
        self.Set_BySettingDictionary(input_dictionary)

    def Get_SettingDictionary(self , recognition_information=None):
        data = RecognitionInfomation()
        if recognition_information==None:
            data = self.setting
        else:
            data = recognition_information
        message={
                "action" : str(data.action) , 
                "end_condition" : str(data.end_condition),
                "execute_number" : data.execute_number
            }
        self.logger.Message_Add(message)
        #ENUMがDictionaryで使えないのでasdictは使えない。
        #setting_dictionary = dataclasses.asdict(data)
        setting_dictionary={
            "action" : self.Set_StringData(data.action,Auto.DATA_TYPE.STRING),
            "end_condition" : self.Set_StringData(data.end_condition,Auto.DATA_TYPE.ENUM),
            "execute_number" : int(data.execute_number),
            "retry_number" : int(data.retry_number),
            "end_action" : self.Set_StringData(data.end_action,Auto.DATA_TYPE.ENUM),
            "image_path" : self.Set_StringData(data.image_path,Auto.DATA_TYPE.STRING),
            "interval_time" : float(data.interval_time),
            "recognition_confidence" : float(data.recognition_confidence),
            "recognition_grayscale" : data.recognition_grayscale
        }
        return setting_dictionary

    def Set_BySettingDictionary(self,input_dictionary):
        action = self.Get_Data("action",Auto.DATA_TYPE.ENUM,input_dictionary)
        end_condition= self.Get_Data("end_condition",Auto.DATA_TYPE.ENUM,input_dictionary)
        execute_number= self.Get_Data("execute_number",Auto.DATA_TYPE.NUMBER,input_dictionary)
        retry_number= self.Get_Data("retry_number",Auto.DATA_TYPE.NUMBER,input_dictionary)
        end_action=self.Get_Data("end_action",Auto.DATA_TYPE.ENUM,input_dictionary)
        image_path=self.Get_Data("image_path",Auto.DATA_TYPE.STRING,input_dictionary)
        interval_time=self.Get_Data("interval_time",Auto.DATA_TYPE.NUMBER,input_dictionary)
        recognition_confidence=self.Get_Data("recognition_confidence",Auto.DATA_TYPE.FLOAT,input_dictionary)
        recognition_grayscale=self.Get_Data("recognition_grayscale",Auto.DATA_TYPE.BOOL,input_dictionary)
        self.setting = RecognitionInfomation(action, end_condition, end_action, execute_number, retry_number, image_path, interval_time, recognition_confidence, recognition_grayscale)

 
    def Get_Data(self, data_name, data_type=Auto.DATA_TYPE.ENUM, data_dictionary=None):
        if data_dictionary is None:
            data_dictionary = self.Get_SettingDictionary()
            
        data_type_mapping = {
            Auto.DATA_TYPE.ENUM: lambda x: Auto.enum_dictionary[x[data_name]],
            Auto.DATA_TYPE.NUMBER: lambda x: int(x[data_name]),
            Auto.DATA_TYPE.BOOL: lambda x: x[data_name],
            Auto.DATA_TYPE.STRING: lambda x: str(x[data_name]),
        }
        
        if data_type in data_type_mapping:
            parameter_value = data_type_mapping[data_type](data_dictionary)
            message = "Get_Data"
            detail_dictionary = {
                "data_name": data_name,
                "parameter_name": parameter_value
            }
            self.logger.Message_Add(message, "INFO", details=detail_dictionary)
            return parameter_value
        else:
            return str(data_dictionary[data_name])
        
        def Set_StringData(self,data,data_type=""):
            if data_type == Auto.DATA_TYPE.ENUM:
                return str(data)
                #return Auto.END_ACTION(data).name
            elif data_type == Auto.DATA_TYPE.NUMBER:
                return str(data)
            elif data_type == Auto.DATA_TYPE.FLOAT:
                return str(data)
            elif data_type == Auto.DATA_TYPE.STRING:
                return  str(data)            
            else:
                return  str(data) 

    def CheckSettingDictionary(self,input_dictionary):
        result_type = {}
        result_type["action"] = type(input_dictionary["action"])
        result_type["end_condition"] = type(input_dictionary["end_condition"])
        result_type["end_action"] = type(input_dictionary["end_action"])
        result_type["execute_number"] = type(input_dictionary["execute_number"])
        result_type["retry_number"] = type(input_dictionary["retry_number"])
        result_type["image_path"] = type(input_dictionary["image_path"])
        result_type["interval_time"] = type(input_dictionary["interval_time"])
        result_type["recognition_confidence"] = type(input_dictionary["recognition_confidence"])
        result_type["recognition_grayscale"] = type(input_dictionary["recognition_grayscale"])
        return result_type
    
    def CheckSetting(self,recognition_information = None):
        result_type = {}
        if(recognition_information==None):
            recognition_information = self.setting
        result_type["action"] = type(recognition_information.action)
        result_type["end_condition"] = type(recognition_information.end_condition)
        result_type["end_action"] = type(recognition_information.end_action)
        result_type["execute_number"] = type(recognition_information.execute_number)
        result_type["retry_number"] = type(recognition_information.retry_number)
        result_type["image_path"] = type(recognition_information.image_path)
        result_type["interval_time"] = type(recognition_information.interval_time)
        result_type["recognition_confidence"] = type(recognition_information.recognition_confidence)
        result_type["recognition_grayscale"] = type(recognition_information.recognition_grayscale)
        return result_type

    action : Auto.ACTION 
    end_condition : Auto.RESULT 
    end_action : Auto.END_ACTION
    execute_number : int = 0
    retry_number : int = 0 
    image_path : str = ""
    interval_time : float = 0.1
    recognition_confidence : float = 1.0
    recognition_grayscale : float = 0
    x_offset_dictionary : dict = None
    y_offset_dictionary : dict = None
            

    def Execute(self):
        result_dictionary={}
        result_action = self.Images_Action_ByInformation(self.setting)
        #Step:Set the result to the data.
        if self.Condition_Judge(result_action,Auto.RESULT.NG):
            result_dictionary["result"]=False
        else:
            result_dictionary["result"]=True
        
        #detailsは詳細内容の辞書。
        #result_details={}
        #result_details["detail"]=str(result_action)
        #result_dictionary["details"]=result_details
        #detailは詳細内容の文字列。
        result_dictionary["detail"]=str(result_action)

        result_error={}
        result_dictionary["error"]=result_error
        return result_dictionary


    def Image_SearchAndXY(self,image_path, recognition_grayscale, recognition_confidence):
        result = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)
        x, y = result
        return x, y
    
    # Imageを探してMouse pointerを移動させる
    def Image_SearchAndMove(self,image_path, x_offset_dictionary, y_offset_dictionary, recognition_grayscale, recognition_confidence):
        try:
            result = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)
            if result is not None:
                x,y=result
                detail_dictionary={}
                if x_offset_dictionary is not None:
                    if image_path in x_offset_dictionary:
                        x_offset = int(x_offset_dictionary[image_path])
                        x = x + x_offset
                        detail_dictionary["offset_x"] = str(x_offset)
                if y_offset_dictionary is not None:
                    if image_path in y_offset_dictionary:
                        y_offset = int(y_offset_dictionary[image_path])
                        y = y + y_offset
                        detail_dictionary["offset_y"] = str(y_offset)
                detail_dictionary["image_path"]= image_path
                pyautogui.moveTo(x, y)
                # Logを貯めて強制終了時にFileを書き込む。
                self.logger.Message_Add( "ImageSearchAndMove","INFO",dettails = detail_dictionary)
                # 毎回LogをFileni書き込む記述（遅いので没）
                #Write_Message(logfile_path , Log_MessageFormat(message))
                return True
            else:
                self.logger.Message_Add("can not find image on screen"+ image_path,"WARNING")
                return False
        except Exception:
            self.logger.error("image read error")
            return False
            exit

    # Mouse Action
    def Action_Execute(self,action):
        if action == Auto.ACTION.CLICK:
            pyautogui.click()
            pyautogui.mouseUp()
        elif action == Auto.ACTION.DOUBLE_CLICK:
            pyautogui.doubleClick()
            pyautogui.mouseUp()

    # 条件判断回路
    def Condition_Judge(self,condition, result):
        # 条件と結果が同じならOK
        if condition == result:
            func_name = inspect.currentframe().f_code.co_name
            args = inspect.getargvalues(inspect.currentframe())[3]
            self.logger.Message_Add("Condition_Judge Result:OK","INFO")
            return True
        # 条件がOKで結果がALL_OKならOK
        elif condition == Auto.RESULT.OK and result == Auto.RESULT.ALL_OK:
            self.logger.Message_Add("Condition_Judge Result:OK(ALL_OK)","INFO")
            return True
        # それ以外はFalse
        else:
            self.logger.Message_Add( "Condition_Judge Result:NG","INFO")
            return False

    Images_Action_Result = {}
    def Images_Action_ResultInit(self,dictionary , detect = 0 , undetect = 0 , total_detect = 0 , total_undetect = 0):
        for dictionary_key in dictionary.keys():
            dictionary[dictionary_key]["detect"] = detect
            dictionary[dictionary_key]["undetect"] = undetect
            #print("Images_Action_ResultInit:"+dictionary_key)
            if dictionary_key not in dictionary:
                dictionary[dictionary_key]["total_detect"] = total_detect
                dictionary[dictionary_key]["total_undetect"] = total_undetect
        #print(dictionary)
        return dictionary
    
    def Images_Action_ResultSet(self,dictionary,dictionary_key,detect,undetect):
        if dictionary_key in dictionary:
            dictionary[dictionary_key]["detect"] += detect
            dictionary[dictionary_key]["undetect"] += undetect
            dictionary[dictionary_key]["total_detect"] += detect
            dictionary[dictionary_key]["total_undetect"] += undetect
            
            dictionary[dictionary_key]["detect_rate"] = Auto.rate(dictionary[dictionary_key]["detect"] , dictionary[dictionary_key]["undetect"])        
            
            dictionary[dictionary_key]["total_detect_rate"] = Auto.rate(dictionary[dictionary_key]["total_detect"] , dictionary[dictionary_key]["total_undetect"])
            dictionary[dictionary_key]["date"] = datetime.datetime.now().strftime ( '%Y/%m/%d(%A) %H:%M' )
        else:
            dictionary[dictionary_key] = {
                "detect" : detect,
                "undetect" : undetect,
                "detect_rate" : Auto.rate(detect,undetect) ,     
                "total_detect" : detect,
                "total_undetect" : undetect,
                "total_detect_rate" : Auto.rate(detect,undetect)   
            }
        return dictionary

    def InfomationToString(self):
        self.Images_Action_Result
        if self.Images_Action_Result is None:
            return ""
        else:
            return str(self.Images_Action_Result).encode().decode("unicode-escape")
        
    def WriteInfomationToJson(self,file_path):
        self.Images_Action_Result
        JSON_Control.WriteDictionary(file_path,self.Images_Action_Result)

    def ReadInfomationFromJson(self,file_path):
        self.Images_Action_Result
        try:
            self.Images_Action_Result = JSON_Control.ReadDictionary(file_path,self.Images_Action_Result)
        except:
            self.Images_Action_Result={}
            self.logger.Message_Add( "[ERROR]ReadInfomationFromJson:Json Read Error","INFO")
        return self.Images_Action_Result

    # Folder内のImageを探してMouse pointerを移動し、行動する
    def Images_Action(self,action , end_action , end_condition , images_path , x_offset_dictionary , y_offset_dictionary , recognition_grayscale , recognition_confidence , interval_time):
        all_ok = True
        all_ng = True
        result = False
        self.Images_Action_Result

        for image_path in glob.glob(images_path):
            # 画像検索とPointer移動
            end_result = self.Image_SearchAndMove(image_path , x_offset_dictionary , y_offset_dictionary , recognition_grayscale , recognition_confidence)
            if end_result:
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,image_path,1,0)        
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,"all_image",1,0)        
                all_ng = False
                self.Action_Execute(action)
                time.sleep(interval_time)

                # 条件成立での中止処理
                if end_action == Auto.END_ACTION.BREAK and end_condition == Auto.RESULT.OK:
                    self.logger.Message_Add( "Images_Action Result_OK Break(" + str(action) + ")")
                    return Auto.RESULT.OK
            else:
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,image_path,0,1)        
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,"all_image",0,1)        
                all_ok = False
                # 条件成立での中止処理
                if end_action == Auto.END_ACTION.BREAK and end_condition == Auto.RESULT.NG:
                    self.logger.Message_Add( "Images_Action Result_NG Break(" + str(action) + ")")
                    return Auto.RESULT.NG
        if all_ok == True:
            return Auto.RESULT.ALL_OK
        elif all_ng == True:
            return Auto.RESULT.NG
        else:
            return Auto.RESULT.OK

    # Images_Actionを繰り返し実行する。
    def Images_Action_ByInformation(self,recognition_information , x_offset_dictionary=None , y_offset_dictionary=None):
        all_ok = True
        all_ng = True
        end_condition = Auto.RESULT.NG
        end_condition_memory = Auto.RESULT.NG
        if x_offset_dictionary is None:
            x_offset_dictionary = recognition_information.x_offset_dictionary 
        if y_offset_dictionary is None:
            y_offset_dictionary = recognition_information.y_offset_dictionary

        continue_flag = True
        loop01 = 0

        while continue_flag == True:
            # 指定回数実行する。
            for loop02 in range(recognition_information.execute_number):
                message={
                    "text" : "Images_Action",
                    "retry" : loop01,
                    "execute_number":str(loop02)+"/"+str(recognition_information.execute_number)
                }
                self.logger.Message_Add(message,"INFO")
                end_result = self.Images_Action(recognition_information.action , recognition_information.end_action , recognition_information.end_condition , recognition_information.image_path,x_offset_dictionary , y_offset_dictionary , recognition_information.recognition_grayscale , recognition_information.recognition_confidence , recognition_information.interval_time)
                if end_result != Auto.RESULT.NG:
                    all_ng = False
                    message={
                        "text" : "Images_Action Continue",
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.Message_Add(message,"INFO")
                else:
                    all_ok = False
                    message={
                        "text" : "Images_Action NG",
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.Message_Add(message,"INFO")
                # 条件成立での中止処理
                if recognition_information.end_action == Auto.END_ACTION.BREAK and recognition_information.end_condition == end_result:
                    message={
                        "text" : "Images_Action BREAK",
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.Message_Add(message,"INFO")
                    break
                # 条件成立での中止処理
                if recognition_information.end_action == Auto.END_ACTION.FOLDER_END_BREAK and recognition_information.end_condition == end_result:
                    message={
                        "text" : "Images_Action FOLDER_END_BREAK",
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.Message_Add(message,"INFO")
                    break
            if self.Condition_Judge(recognition_information.end_condition , end_result) == False and loop01 < recognition_information.retry_number:
                message={
                    "text" : "Images_Action False and retry",
                    "result" : Auto.RESULT(end_result).name,
                    "retry" : loop01,
                    "execute_number":str(loop02)+"/"+str(recognition_information.execute_number)
                }
                self.logger.Message_Add(message,"INFO")
                continue_flag = True
            else:
                message={
                    "text" : "Images_Action EndResult",
                    "result" : Auto.RESULT(end_result).name,
                    "retry" : loop01,
                    "execute_number":str(loop02)+"/"+str(recognition_information.execute_number)
                }
                self.logger.Message_Add(message,"INFO")
                continue_flag = False
            loop01 = loop01 + 1
        Log.Write_MessageList(logfile_path , message_list)
        message_list.clear()
        if all_ok == True:
            return Auto.RESULT.ALL_OK
        elif all_ng == True:
            return Auto.RESULT.NG
        else:
            return Auto.RESULT.OK

    def Images_Action_BySettingDictionary(self,setting = {}):
        setting=RecognitionInfomation()
        if setting == {} :
            setting.Get_SettingDictionary(setting)

    # 条件が成立した時に繰り返し実行する。
    def Images_ConditionCheckAndAction(self,name , condition , action_recognition_information , x_offset_dictionary , y_offset_dictionary):
        action_result = Auto.RESULT.NG
        # 条件を比較
        action_condition = False
        if action_recognition_information.end_condition == condition:
            action_condition = True
        elif action_recognition_information.end_condition == Auto.RESULT.ALL_OK:
            if condition == Auto.RESULT.OK:
                action_condition = True
        # 条件を比較して成立したら実行
        if action_condition == True:
            self.logger.Message_Add( "Images_ConditionCheckAndAction:実行条件成立:" + name)
            action_result = self.Images_Action_ByInformation(action_recognition_information , x_offset_dictionary , y_offset_dictionary)
        return action_result

    def Image_AroundMouse(self,file_path , flag_overwrite=True , wide=0 , height=0 , dupplicate_format="{}({:0=3}){}"):
        x , y = pyautogui.position()
        self.Image_AroundPoint(file_path , flag_overwrite , x , y , wide , height , dupplicate_format)

    def Image_AroundPoint(self,file_path , flag_overwrite=True , x=0 , y=0 , wide=0 , height=0 , dupplicate_format="{}({:0=3}){}"):
        if flag_overwrite == False:
            path = Rename.duplicate_rename(file_path , dupplicate_format)
        else:
            path = file_path
        if wide == 0 or height == 0:
            PIL.ImageGrab.grab().save(path)
        else:
            bbox_w = wide
            bbox_h = height
            bbox_x = max(0 , x - bbox_w/2)
            bbox_y = max(0 , y - bbox_h/2)
            PIL.ImageGrab.grab(bbox=(bbox_x , bbox_y , bbox_x +
                            bbox_w , bbox_y + bbox_h)).save(path)
