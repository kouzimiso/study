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

#文字列のAction名と設定辞書で動作するだけの関数
class Action:
    settings : dict ={}
    def __init__(self , setting_dictionary ={}) -> None:
        result_dictionary = self.settings = setting_dictionary

    def Execute(self, type = "" , setting_dictionary = None):
        if setting_dictionary is None:
            setting_dictionary = self.settings
        result_dictionary={}

        if (type == "ExecuteProgram"):
            result_dictionary = ExecuteProgram.ExecuteProgram(setting_dictionary)
        elif (type == "Recognition"):
            recognition = Recognition.Recognition(setting_dictionary)
            result_dictionary = recognition.Execute()
        elif (type == "Image"):
            result_dictionary=ImageControl.Execute(setting_dictionary)
        elif (type == "CheckDay"):
            week_day = Weekday.DayOfTheWeek(setting_dictionary = setting_dictionary)
            result_dictionary = week_day.CheckDay(setting_dictionary)
            
        elif (type == "ShutDown"):
            shutdown()
            result_dictionary={
                "detail" : "ShutDown"
            }

        elif (type == "Reboot"):
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
