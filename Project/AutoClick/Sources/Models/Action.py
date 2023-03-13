import enum
import sys
import os
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
            os.system('shutdown -r -f')
            result_dictionary["result"] = True

            result_detail={}
            result_detail["detail"]="ShutDown"
            result_dictionary["detail"]=result_detail

            result_error={}
            result_dictionary["error"]=result_error

        return result_dictionary


