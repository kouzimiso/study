import enum
import sys
import os
import platform
sys.path.append("../Common")
sys.path.append("../../Common")
import auto
import Recognition
import weekday
#文字列のAction名と設定辞書で動作するだけの関数
class Action:
    settings : dict ={}
    def __init__(self , setting_dictionary ={}) -> None:
        self.settings = setting_dictionary

    def Execute(self, type = "" , setting_dictionary = None):
        if setting_dictionary is None:
            setting_dictionary = self.settings
        result_dictionary={}

        if (type == "Recognition"):
            recognition = Recognition.Recognition(setting_dictionary)
            result_dictionary=recognition.Execute()
        
        elif (type == "Check_Day"):
            week_day = weekday.DayOfTheWeek(setting_dictionary = setting_dictionary)
            result_dictionary = week_day.Check_Day(setting_dictionary)
            
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
