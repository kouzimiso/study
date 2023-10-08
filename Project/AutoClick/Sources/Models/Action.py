import enum
import sys
import os
import platform
sys.path.append("Common")
sys.path.append("../Common")
sys.path.append("../../Common")
import Recognition
import ImageControl
import Weekday
import ExecuteProgram
import FunctionUtility
#文字列のAction名と設定辞書で動作するだけの関数
class Action:
    settings : dict ={}
    default_settings :dict = {
        "type":"ExecuteProgram",
        "program_path":"",
        "argument1":""
    }
    def __init__(self , settings_dictionary ={}) -> None:
        result_dictionary = self.settings = settings_dictionary

    def Get_SettingsDictionary(self):
        return self.settings

    def Set_BySettingsDictionary(self,settings_dictionary):
        self.settings = {**self.default_settings, **settings_dictionary}       
        #設定の読込
        #-----------------
        #機能実行 
        result_dictionary = {}
        result_dictionary["result"] = True
        return result_dictionary

    def Execute(self, type = "" , settings_dictionary = None):
        #設定の読込
        if settings_dictionary is None:
            settings_dictionary = self.settings
        #機能実行 
        result_dictionary={}
        function_dictionary = self.Get_FunctionDictionary()
        try:
            result_dictionary = function_dictionary[self.task_type](settings_dictionary)
        except :
            result_dictionary = {"result":False}
        return result_dictionary
    
    def ArgumentGet(self):
        settings_dictionary = FunctionUtility.ArgumentGet(self.default_settings,self.settings)
        self.settings = {**self.settings, **settings_dictionary}
        self.Set_BySettingsDictionary(self.settings)

    ####専用機能呼び出し####
    def Get_FunctionDictionary(self):
        self.function_dictionary = {
            "ExecuteProgram":self.Call_ExecuteProgram,
            "Recognition":self.Call_Recognition,
            "Image": self.Call_Image,
            "CheckDay":self.Call_CheckDay,
            "ShutDown":self.Call_ShutDown,
            "Reboot":self.Call_Reboot

        }
        return self.function_dictionary
    
    def Call_ExecuteProgram(self , settings_dictionary):
        result_dictionary = ExecuteProgram.ExecuteProgram(settings_dictionary)
        return result_dictionary

    def Call_Recognition(self , settings_dictionary):
        recognition = Recognition.Recognition(settings_dictionary)
        result_dictionary = recognition.Execute()
        return result_dictionary

    def Call_Image(self , settings_dictionary):
        result_dictionary=ImageControl.Execute(settings_dictionary)
        return result_dictionary


    def Call_CheckDay(self , settings_dictionary):
        week_day = Weekday.DayOfTheWeek(settings_dictionary = settings_dictionary)
        result_dictionary = week_day.CheckDay(settings_dictionary)
        return result_dictionary

    def Call_ShutDown(self , settings_dictionary):
        shutdown()
        result_dictionary={
            "detail" : "ShutDown"
        }
        return result_dictionary


    def Call_Reboot(self , settings_dictionary):
        reboot()
        result_dictionary={
            "detail" : "Reboot"
        }
        return result_dictionary

def shutdown():
    if platform.system() == "Windows":
        os.system("shutdown /s /t 1")
        return True
    elif platform.system() == "Linux":
        os.system("sudo shutdown -h now")
        return True
    else:
        return False  

def reboot():
    if platform.system() == "Windows":
        os.system("shutdown /r /t 1")
        return True
    elif platform.system() == "Linux":
        os.system("sudo shutdown -r now")
        return True
    else:
        return False  

    #command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    class_instance = Action()
    class_instance.ArgumentGet()
    result_dictionary = class_instance.Execute()
    FunctionUtility.Result(result_dictionary)
    
if __name__ == '__main__':
    main()
