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
_list = []
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

    def __init__(self, setting_dictionary = {}):
        #self.setting=RecognitionInfomation(**setting_dictionary)
        self.logger = Log.Logs(setting_dictionary)
        self.logger.log("Start Recognition","INFO",details=setting_dictionary)
        self.Set_BySettingDictionary(setting_dictionary)

    def Get_SettingDictionary(self , recognition_information=None):
        data = RecognitionInfomation()
        if recognition_information==None:
            data = self.setting
        else:
            data = recognition_information
        details={
                "action" : str(data.action) , 
                "end_condition" : str(data.end_condition),
                "execute_number" : data.execute_number
            }
        self.logger.log("Get_SettingDictionary","DEBUG",details = details)
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
        if input_dictionary is None:
            input_dictionary = self.Get_SettingDictionary()
        action = self.Get_Data("action",Auto.DATA_TYPE.ENUM,input_dictionary,Auto.ACTION.NONE)
        end_condition= self.Get_Data("end_condition",Auto.DATA_TYPE.ENUM,input_dictionary,Auto.END_ACTION.BREAK)
        execute_number= input_dictionary.get("execute_number",0)
        retry_number= input_dictionary.get("retry_number",0)
        end_action=self.Get_Data("end_action",Auto.DATA_TYPE.ENUM,input_dictionary,0)
        image_path=input_dictionary.get("image_path","")
        interval_time= input_dictionary.get("interval_time",0)
        recognition_confidence=input_dictionary.get("recognition_confidence",0)
        recognition_grayscale=input_dictionary.get("recognition_grayscale",False)
        self.setting = RecognitionInfomation(action, end_condition, end_action, execute_number, retry_number, image_path, interval_time, recognition_confidence, recognition_grayscale)

    def Get_Data(self, data_name, data_type=Auto.DATA_TYPE.ENUM, data_dictionary={} ,default_value=""):
        message="Get_Data_Start"
        detail_dictionary = {"data_name" : data_name}
        self.logger.log(message, "DEBUG", details=detail_dictionary)
            
      #  data_type_mapping = {
      #      Auto.DATA_TYPE.ENUM: lambda x: Auto.enum_dictionary[x[data_name]],
      #      Auto.DATA_TYPE.NUMBER: lambda x: int(x[data_name]),
       #     Auto.DATA_TYPE.BOOL: lambda x: x[data_name],
       #     Auto.DATA_TYPE.STRING: lambda x: str(x[data_name]),
       # }
        data_type_mapping = {
            Auto.DATA_TYPE.ENUM: lambda x: Auto.enum_dictionary.get(data_dictionary.get(x,"")),
            #Auto.DATA_TYPE.ENUM: Auto.enum_dictionary[data_dictionary.get(data_name,0)],
            Auto.DATA_TYPE.NUMBER: lambda x:str(data_dictionary[x]),
            Auto.DATA_TYPE.BOOL : lambda x: data_dictionary[x],
            Auto.DATA_TYPE.STRING : lambda x: str(data_dictionary[x])
        }
        
        if data_type in data_type_mapping:
            try:

                parameter_value = data_type_mapping[data_type](data_name)
                message = "Get_Data_Result"
                detail_dictionary = {
                    "data_name": data_name,
                    "data_value": str(parameter_value)
                }
                self.logger.log(message, "DEBUG", details = detail_dictionary)
                return parameter_value
            except:
                return default_value
            
        else:
            return str(data_dictionary.get(data_name,""))
        
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
    def Get_Enum(self,data_name,data_dictionary):
        value = data_dictionary.get(data_name,0)
        print(value)
        return Auto.enum_dictionary[value]

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
        if Auto.Condition_Judge(result_action,Auto.RESULT.NG):
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
        self.logger.MessageList_Write()
        self.logger.MessageList_Clear()

        return result_dictionary


    def Image_SearchAndXY(self,image_path, recognition_grayscale, recognition_confidence):
        result = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)
        x, y = result
        return x, y
    
    # Imageを探してMouse pointerを移動させる
    def Image_SearchAndMove(self,image_path, x_offset_dictionary, y_offset_dictionary, recognition_grayscale, recognition_confidence):
        try:
            result_detail = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)
            if result_detail is not None:
                x,y=result_detail
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
                self.logger.log( "ImageSearchAndMove","INFO",details = detail_dictionary)
                return True
            else:
                detail_dictionary={"image_path": image_path}
                self.logger.log("can not find image on screen","INFO",details = detail_dictionary)
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
            self.logger.log( "[ERROR]ReadInfomationFromJson:Json Read Error","INFO")
        return self.Images_Action_Result

    # Folder内のImageを探してMouse pointerを移動し、行動する
    def Images_Action(self,action , end_action , end_condition , images_path , x_offset_dictionary , y_offset_dictionary , recognition_grayscale , recognition_confidence , interval_time):
        all_ok = True
        all_ng = True
        none = True
        self.Images_Action_Result
        path_list = glob.glob(images_path)
        #abs_path = os.path.abspath(images_path)
        #print("####"+abs_path+":"+",".join(path_list))
        #for image_path in path_list:
        for image_path in glob.glob(images_path):
            none = False
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
                    self.logger.log( "Images_Action Result_OK Break(" + str(action) + ")")
                    return Auto.RESULT.OK
            else:
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,image_path,0,1)        
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,"all_image",0,1)        
                all_ok = False
                # 条件成立での中止処理
                if end_action == Auto.END_ACTION.BREAK and end_condition == Auto.RESULT.NG:
                    self.logger.log( "Images_Action Result_NG Break(" + str(action) + ")")
                    return Auto.RESULT.NG
        if none:
            return Auto.RESULT.NONE
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
        end_result = Auto.RESULT.NONE
        end_condition = Auto.RESULT.NG
        end_condition_memory = Auto.RESULT.NG
        if x_offset_dictionary is None:
            x_offset_dictionary = recognition_information.x_offset_dictionary 
        if y_offset_dictionary is None:
            y_offset_dictionary = recognition_information.y_offset_dictionary

        continue_flag = True
        loop01 = 0
        loop02 = 0

        while continue_flag == True:
            # 指定回数実行する。
            for loop02 in range(recognition_information.execute_number):
                message="Images_Action"
                details={
                    "retry" : loop01,
                    "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number),
                    "file_path": recognition_information.image_path
                }
                self.logger.log(message,"INFO",details=details)
                end_result = self.Images_Action(recognition_information.action , recognition_information.end_action , recognition_information.end_condition , recognition_information.image_path,x_offset_dictionary , y_offset_dictionary , recognition_information.recognition_grayscale , recognition_information.recognition_confidence , recognition_information.interval_time)
                if end_result == Auto.RESULT.NONE:
                    all_ok = False
                    all_ng = True
                    message="Images_Actction image is None"
                    details={
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.log(message,"INFO",details)
                elif end_result != Auto.RESULT.NG:
                    all_ng = False
                    message="Images_Action complete and Continue"
                    details={
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.log(message,"INFO",details)
                else:
                    all_ok = False
                    message="Images_Action NG"
                    details={
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.log(message,"INFO",details)
                # 条件成立での中止処理
                if recognition_information.end_action == Auto.END_ACTION.BREAK and recognition_information.end_condition == end_result:
                    message="Images_Action complete and BREAK"
                    details={
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.log(message,"INFO",details)
                    break
                # 条件成立での中止処理
                if recognition_information.end_action == Auto.END_ACTION.FOLDER_END_BREAK and recognition_information.end_condition == end_result:
                    message="Images_Action complete and FOLDER_END_BREAK"
                    details={
                        "result" : Auto.RESULT(end_result).name,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number)
                    }
                    self.logger.log(message,"INFO",details)
                    break
            judge_detail={}
            judge_result = Auto.Condition_Judge(recognition_information.end_condition , end_result,details = judge_detail)
            self.logger.log("Judge Result" , "INFO", details = judge_detail)
            if judge_result == False and loop01 < recognition_information.retry_number:
                message="Images_Action False and retry"
                details={
                    "result" : Auto.RESULT(end_result).name,
                    "retry" : loop01,
                    "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number)
                }
                self.logger.log(message,"INFO",details)
                continue_flag = True
            else:
                continue_flag = False
            loop01 = loop01 + 1
        if all_ok == True:
            result_detail = Auto.RESULT.ALL_OK
        elif all_ng == True:
            result_detail = Auto.RESULT.NG
        else:
            result_detail = Auto.RESULT.OK
        message="Images_Action End."
        details={
            "result" : Auto.RESULT(result_detail).name,
            "retry" : loop01,
            "execute_number":str(loop02+1)+"/"+str(recognition_information.execute_number)
        }
        self.logger.log(message,"INFO",details)
        return result_detail

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
            self.logger.log( "Images_ConditionCheckAndAction:実行条件成立:" + name)
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
def main():
    setting_dictionary={}
    recognition = Recognition.Recognition(setting_dictionary)
    result_dictionary=recognition.Execute()


if __name__ == "__main__":
    sys.exit(main())
