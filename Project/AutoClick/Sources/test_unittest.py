## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import sys
import os
import datetime
import pyautogui
import cv2
import json
import clr
import PIL
import unittest
import socket
import threading
import dataclasses
import re

sys.path.append("./Common")
sys.path.append("./Models")
sys.path.append("./ViewModels")
sys.path.append("./Views")

import Log
import ADB
import OCR
import Auto
import Weekday
import xml.dom.minidom
import ImageControl
import FileControl
import Scheduler
import Task
import Action
import Parser
import Judge
import Recognition


class Test(unittest.TestCase):
    def setUp(self):
        self.logger = Log.Logs()
        
    def test_unittest_assertEqual(self):
        function_name=sys._getframe().f_code.co_name
        
        self.logger.log("["+function_name+"]"+"assert命令自体のTest")
        num=3
        expected =6
        actual=2*num
        self.assertEqual(expected,actual)

    def test_split(self):
        #"Searater複数個を含めて文字列をsplitで分割する正規表現(***|***|***)"
        text="水曜日10:20<=Now<=月曜日22:30"
        text_list =re.split("(==|<=|>=|<>|<|=|>)",text)
        print(text_list)
        
        expected =["水曜日10:20","<=","Now","<=","月曜日22:30"]
        actual= text_list
        self.assertEqual(expected,actual)
        
    def test_split2(self):
        data_dictioanry={"月曜日":1,"火曜日":{"type":"曜日","name":"Turesday"},"水曜日":3}
        text="水曜日10:20<=Now<=月曜日22:30"
        regular_expression = ""
        for key in data_dictioanry.keys():
            if regular_expression == "":
                regular_expression="(" + key
            else:
                regular_expression = regular_expression + "|" +key
        regular_expression = regular_expression + ")"
        text_list =re.split(regular_expression , text)
        text_list.remove("")
        print (text_list)
                
        expected =text_list
        parser = Parser.Parser()
        actual= parser.SplitByDictionary(text,data_dictioanry)
        self.assertEqual(expected,actual)

    def test_parser(self):
        information={
            "Result_DayCondition1":{"result" : True , "detail" : ""},
            "Result_DayCondition2":{"result" : False , "detail" : ""},
            "Result_DayCondition3":{ "detail" : ""},
            "Result_DayCondition4":{ "detail" : "Result.OK"}
        }
        judge_instance = Judge.Judge()

        expression="Result_DayCondition1=True"
        result=judge_instance.Result_ByDictionaryInformation(expression,information)
        expected = True
        actual= result
        self.assertEqual(expected,actual)

        expression="Result_DayCondition2=True"
        result=judge_instance.Result_ByDictionaryInformation(expression,information)
        expected = False
        actual= result
        self.assertEqual(expected,actual)

        expression="Result_DayCondition3=None"
        result=judge_instance.Result_ByDictionaryInformation(expression,information)
        expected = True
        actual= result
        self.assertEqual(expected,actual)
        
        expression="Result_DayCondition1=True,Result_DayCondition2=True"
        result=judge_instance.Result_ByDictionaryInformation(expression,information)
        expected = True
        actual= result
        self.assertEqual(expected,actual)
        
        expression="Result_DayCondition4.detail=Result.OK"
        result=judge_instance.Result_ByDictionaryInformation(expression,information)
        expected = True
        actual= result
        self.assertEqual(expected,actual)

    def test_weekday(self):
        details = {}
        week_day = Weekday.DayOfTheWeek()
        result =week_day.StringDateTimeToDatetime("2003/4/14 22:00:30",details)

        expected = datetime.datetime(2003,4,14,22,00,30)
        actual= result
        self.assertEqual(expected,actual)

        expected = "DateTime"
        actual= details["type"]
        self.assertEqual(expected,actual)

        week_day = Weekday.DayOfTheWeek()
        result =week_day.StringDateTimeToDatetime("22:00",details)
        expected = datetime.time(22,00)
        actual= result
        self.assertEqual(expected,actual)
        setting={
            "log_print_standard_output" : True,
            "log_file_path_list":"../Log/log_test_all.log",
            "log_function":True,
            "day1" :"木曜10:20",
            "day2" :"2023/3/9 10:30:10",
            "day3" :"Friday 22:30"
        }
        result = week_day.CheckDay(setting)
        expected = True
        actual= result["result"]
        self.assertEqual(expected,actual)

    def test_weekday2(self):
        plan_lists_dictionary={
            "test1" :
            [
                {
                    "name": "TimeCheck_2",
                    "type": "CheckDay",
                    "result_name":"Time_Check2",
                    "settings": {
                        "day1": "月曜日0:00",
                        "day2": "Now",
                        "day3": "月曜日24:00",
                        "log_print_standard_output": True,"log_function":True,"log_file_path_list": "../Log/log_unittest.json",
                        "#step_check_mode" : True
                    }
                },
                {
                    "name": "TimeCheck_3",
                    "type": "CheckDay",
                    "result_name":"Time_Check3",
                    "settings": {
                        "day1": "火曜日0:00",
                        "day2": "Now",
                        "day3": "木曜日24:00",
                        "log_print_standard_output": False,"log_function":True,"log_file_path_list": "../Log/log_unittest.json",
                        "#step_check_mode" : True,
                    }
                },
                {
                    "name": "TimeCheck_4",
                    "type": "CheckDay",
                    "result_name":"Time_Check4",
                    "settings": {
                        "day1": "金曜日0:00",
                        "day2": "Now",
                        "day3": "日曜日24:00",
                        "log_print_standard_output": True,"log_function":True,"log_file_path_list": "../Log/log_unittest.json",
                        "#step_check_mode" : True
                    }
                },
                {
                    "name": "Condition_Execute",
                    "result_name": "Condition_Execute01",
                    "type": "Judge",
                    "settings": {
                        "condition_list": [
                            "Time_Check1=True,Time_Check2=True,Time_Check3.result=True,Time_Check4.result=True"
                        ],
                        "log_print_standard_output": True,"log_function":True,"log_file_path_list": "../Log/log_unittest.json",
                        "#step_check_mode" : True,"step_check_comment":"The following statement will always be true if it is currently Monday, Tuesday through Wednesday, or Friday through Sunday. "
                    }
                },
                {
                    "name": "Condition_Execute",
                    "result_name": "Condition_Execute",
                    "type": "Judge",
                    "settings": {
                        "condition_list": [
                            "Time_Check1=True,Time_Check2=True,Time_Check3.result=True,Time_Check4.result=True",
                            "Condition_Execute01 = true"
                        ],
                        "log_print_standard_output": True,"log_function":True,"log_file_path_list": "../Log/log_unittest.json",
                        "#step_check_mode" : True,"step_check_comment":"The results Time check and Time check Judge are True and you should get a True result."
                    }
                },
                {
                    "name": "Test_ExecuteProgram",
                    "type": "ExecuteProgram",
                    "result_name":"",
                    "condition_list":["Condition_Execute = true"],
                    "settings": {
                        "program_path": "./Resources/Camera.exe",
                        "file_path": "../Log/capture.png",
                        "log_print_standard_output": False,"log_function":True,"log_file_path_list": "../Log/log_camera.json",
                        "step_check_mode" : False,"step_check_comment":""
                    }
                },

                {
                    "name": "ClickTest01",
                    "type": "Recognition",
                    "result_name":"Result_ClickTest01",
                    "condition_list":["Condition_Execute = true"],
                    "settings": {
                        "action": "ACTION.DOUBLE_CLICK",
                        "end_condition": "RESULT.OK",
                        "end_action": "END_ACTION.BREAK",
                        "execute_number": 2,
                        "retry_number": 0,
                        "image_path": "../Images/image01/*.png",
                        "interval_time": 10,
                        "recognition_confidence": 0.99,
                        "recognition_gray_scale": True,
                        "log_print_standard_output": True,"log_function":True,"log_file_path_list": "../Log/log_recognition.json",
                        "#step_check_mode" : True,"step_check_comment":"NGになる予定のClick Teskです。標準出力は有効。"
                    }
                },
                {
                    "name": "ClickTest02-1",
                    "type": "Recognition",
                    "condition_list":["Condition_Execute = true","Result_ClickTest01.detail=RESULT.NG"],
                    "result_name":"Result_AccountClicked",
                    "settings": {
                        "action": "ACTION.DOUBLE_CLICK",
                        "end_condition": "RESULT.OK",
                        "end_action": "END_ACTION.BREAK",
                        "execute_number": 2,
                        "retry_number": 0,
                        "image_path": "../Images/image01/*.png",
                        "interval_time": 10,
                        "recognition_confidence": 0.99,
                        "recognition_gray_scale": True,
                        "log_print_standard_output": False,"log_function":True,"log_file_path_list": "../Log/log_recognition.json",
                        "#step_check_mode" : True,"step_check_comment":"同じくNGになる予定のClick Teskです。標準出力は無効。"
                    }
                },
                {
                    "name" : "HouchiPlanStart",
                    "type" : "RunPlanLists",
                    "condition_list":["Condition_Execute = true","Result_ClickTest01.detail=RESULT.NG"],
                    "result_name":"",
                    "settings" : {
                        "file_path"  : "../Setting/RunHouchi.json",
                        "log_function":True,"log_print_standard_output": True,"log_file_path_list": "../Log/log_RunPlanList.json.json",
                        "#step_check_mode" : True,
                        "run_plan_name_list" : [
                            "CallSetting"
                        ]
                    }
                }
            ],
            "CallSetting" :
            [
                {
                    "name": "ClickTest02-2",
                    "type": "Recognition",
                    "result_name":"Result_AccountClicked",
                    "condition_list":["Condition_Execute = true","Result_ClickTest01.detail=RESULT.NG"],
                    "settings": {
                        "action": "ACTION.DOUBLE_CLICK",
                        "end_condition": "RESULT.OK",
                        "end_action": "END_ACTION.BREAK",
                        "execute_number": 2,
                        "retry_number": 0,
                        "image_path": "../Images/image01/*.png",
                        "interval_time": 10,
                        "recognition_confidence": 0.99,
                        "recognition_gray_scale": True,
                        "log_print_standard_output": False,"log_function":True,"log_file_path_list": "../Log/log_recognition.json",
                        "#step_check_mode" : True,"step_check_comment":"同じくNGになる予定のClick Teskです。標準出力は無効。"
                    }
                }
            ]
        }
        task = Task.Task("")
        information = task.Run( "test1","" , plan_lists_dictionary)
         
#Main Program実行部
def main():
    unittest.main()

if __name__ == "__main__":
    sys.exit(main())
