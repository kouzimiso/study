## $python 画像自動Click ##
# 設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import time
import datetime
import sys
import os
import pyautogui
import PIL
import glob
sys.path.append("../Common")
sys.path.append("../../Common")
import Rename
import Log
import JSON_Control
import Auto

# log関係

logfile_path = os.path.dirname(__file__)+'/../../Log/log_auto.txt'

class Recognition:
    default_setting :dict = {
        # 処理
        "action" : "CLICK",#"double_CLICK",""
        # 終了条件
        "end_condition" : "",
        # 実行回数
        "execute_number" : 0,
        # 再試行回数
        "retry_number" : 0,
        # 終了処理
        "end_action" : "continue",#
     
        # クリックする画像を保存するフォルダ
        "image_path" : "",
        # 画像をClickした後の待ち時間(秒)
        "interval_time":  0.1,
        # 画像認識のあいまい設定
        "recognition_confidence" : 1.0,
        # GrayScale設定(高速化)
        "recognition_grayscale" : 0
    }
    def __init__(self, setting_dictionary={}):
        self.logger = Log.Logs(setting_dictionary)
        self.logger.log("Start Recognition","INFO",details=setting_dictionary)
        self.Set_BySettingDictionary(setting_dictionary)

  
    def Get_SettingDictionary(self):

        return self.setting


    def Set_BySettingDictionary(self,input_dictionary):
        self.setting = {**self.default_setting, **input_dictionary}
        

    def Execute(self):
        result_dictionary={}
        result_action = self.Images_Action_ByInformation(self.setting)
        #Step:Set the result to the data.
        if Auto.Condition_Judge(result_action,"NG"):
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
    def Image_SearchAndMove(self,image_path, x_offset_dictionary, y_offset_dictionary, recognition_grayscale, recognition_confidence,detail_dictionary = {}):
        try:
            result_detail = pyautogui.locateCenterOnScreen(image_path, grayscale=recognition_grayscale, confidence=recognition_confidence)

            if result_detail is not None:
                x,y=result_detail
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
        if action == 'CLICK':
            pyautogui.click()
            pyautogui.mouseUp()
        elif action == 'DOUBLE_CLICK':
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

    def InformationToString(self):
        self.Images_Action_Result
        if self.Images_Action_Result is None:
            return ""
        else:
            return str(self.Images_Action_Result).encode().decode("unicode-escape")
        
    def WriteInformationToJson(self,file_path):
        self.Images_Action_Result
        JSON_Control.WriteDictionary(file_path,self.Images_Action_Result)

    def ReadInformationFromJson(self,file_path):
        self.Images_Action_Result
        try:
            self.Images_Action_Result = JSON_Control.ReadDictionary(file_path,self.Images_Action_Result)
        except:
            self.Images_Action_Result={}
            self.logger.log( "[ERROR]ReadInformationFromJson:Json Read Error","INFO")
        return self.Images_Action_Result

    # Folder内のImageを探してMouse pointerを移動し、行動する
    def Images_Action(self,action , end_action , end_condition , images_path , x_offset_dictionary , y_offset_dictionary , recognition_grayscale , recognition_confidence , interval_time):
        all_ok = True
        all_ng = True
        none = True
        self.Images_Action_Result
        #path_list = glob.glob(images_path)
        #abs_path = os.path.abspath(images_path)
        #print("####"+abs_path+":"+",".join(path_list))
        #for image_path in path_list:
        for image_path in glob.glob(images_path):
            image_path = image_path.replace('\\', '/')
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
                if end_action == "BREAK" and end_condition == "OK":
                    self.logger.log( "Images_Action Result_OK Break(" + str(action) + ")")
                    return "OK"
            else:
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,image_path,0,1)        
                self.Images_Action_Result=self.Images_Action_ResultSet(self.Images_Action_Result,"all_image",0,1)        
                all_ok = False
                # 条件成立での中止処理
                if end_action == "BREAK" and end_condition == "NG":
                    self.logger.log( "Images_Action Result_NG Break(" + str(action) + ")")
                    return "NG"
        if none:
            return "NONE"
        if all_ok == True:
            return "ALL_OK"
        elif all_ng == True:
            return "NG"
        else:
            return "OK"

    # Images_Actionを繰り返し実行する。
    def Images_Action_ByInformation(self,recognition_information , x_offset_dictionary=None , y_offset_dictionary=None):
        all_ok = True
        all_ng = True
        end_result = "NONE"
        end_condition = "NG"
        end_condition_memory = "NG"
        if x_offset_dictionary is None:
            x_offset_dictionary = recognition_information.get("x_offset_dictionary")
        if y_offset_dictionary is None:
            y_offset_dictionary = recognition_information.get("y_offset_dictionary")

        continue_flag = True
        loop01 = 0
        loop02 = 0

        while continue_flag == True:
            # 指定回数実行する。
            for loop02 in range(recognition_information.get("execute_number")):
                message="Images_Action"
                details={
                    "retry" : loop01,
                    "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number")),
                    "image_path": recognition_information.get("image_path")
                }
                self.logger.log(message,"INFO",details=details)
                end_result = self.Images_Action(recognition_information.get("action") , recognition_information.get("end_action") , recognition_information.get("end_condition") , recognition_information.get("image_path"),x_offset_dictionary , y_offset_dictionary , recognition_information.get("recognition_grayscale") , recognition_information.get("recognition_confidence") , recognition_information.get("interval_time"))
                if end_result == "NONE":
                    all_ok = False
                    all_ng = True
                    message="Images_Actction image is None"
                    details={
                        "result" : end_result,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number"))
                    }
                    self.logger.log(message,"INFO",details)
                elif end_result != "NG":
                    all_ng = False
                    message="Images_Action complete and Continue"
                    details={
                        "result" : end_result,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number"))
                    }
                    self.logger.log(message,"INFO",details)
                else:
                    all_ok = False
                    message="Images_Action NG"
                    details={
                        "result" : end_result,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number"))
                    }
                    self.logger.log(message,"INFO",details)
                # 条件成立での中止処理
                if recognition_information.get("end_action") == "BREAK" and recognition_information.get("end_condition") == end_result:
                    message="Images_Action complete and BREAK"
                    details={
                        "result" : end_result,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number"))
                    }
                    self.logger.log(message,"INFO",details)
                    break
                # 条件成立での中止処理
                if recognition_information.get("end_action") == "FOLDER_END_BREAK" and recognition_information.get("end_condition") == end_result:
                    message="Images_Action complete and FOLDER_END_BREAK"
                    details={
                        "result" : end_result,
                        "retry" : loop01,
                        "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number"))
                    }
                    self.logger.log(message,"INFO",details)
                    break
            judge_detail={}
            judge_result = Auto.Condition_Judge(recognition_information.get("end_condition") , end_result,details = judge_detail)
            self.logger.log("Judge Result" , "INFO", details = judge_detail)
            if judge_result == False and loop01 < recognition_information.get("retry_number"):
                message="Images_Action False and retry"
                details={
                    "result" : end_result,
                    "retry" : loop01,
                    "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number"))
                }
                self.logger.log(message,"INFO",details)
                continue_flag = True
            else:
                continue_flag = False
            loop01 = loop01 + 1
        if all_ok == True:
            result_detail = "ALL_OK"
        elif all_ng == True:
            result_detail = "NG"
        else:
            result_detail = "OK"
        message="Images_Action End."
        details={
            "result" : result_detail,
            "retry" : loop01,
            "execute_number":str(loop02+1)+"/"+str(recognition_information.get("execute_number"))
        }
        self.logger.log(message,"INFO",details)
        return result_detail

    # 条件が成立した時に繰り返し実行する。
    def Images_ConditionCheckAndAction(self,name , condition , action_recognition_information , x_offset_dictionary , y_offset_dictionary):
        action_result = "NG"
        # 条件を比較
        action_condition = False
        if action_recognition_information.get("end_condition") == condition:
            action_condition = True
        elif action_recognition_information.get("end_condition") == "ALL_OK":
            if condition == "OK":
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
    recognition = Recognition(setting_dictionary)
    result_dictionary=recognition.Execute()


if __name__ == "__main__":
    sys.exit(main())
