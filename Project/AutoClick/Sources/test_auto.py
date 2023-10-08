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
import XML_Control
import xml.dom.minidom

import ImageControl
import JSON_Control
import FileControl
import Scheduler
import Task
import Action
import Parser
import Judge
import Recognition

#log関係
message_list=[]
logfile_path='../Log/log_test_auto.json'#準備必要問題:Folder

check_planlist={
	"Start": 
	[
		{
			"name" : "StartTask",
		 	"type" : "RunPlanLists",
		 	"settings" : {
				"file_path" : "",
				"plan_lists" : [
					"HotSpotON",
			 		"Mementomori",
 					"Houchi",
					"ShutDown"
				]
			}
		}
	],

	"ShutDown":
	[
		{
			"name": "ShutDown",
			"type": "ShutDown",
			"settings": {}
		}
	]	
}


class Test(unittest.TestCase):
    def test_unittest_assertEqual(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"assert命令自体のTest")
        num=3
        expected =6
        actual=2*num
        self.assertEqual(expected,actual)


    def test_Auto5_dictionarytodata(self):
        settings_dictionary = {
            "action" : "ACTION.CLICK" ,
            "end_condition" : "RESULT.OK",
            "execute_number" : 1,
            "retry_number" : 1,
            "end_action" : "END_ACTION.CONTINUE",
            "image_path" : "../Images/test/*.png",
            "interval_time" : 1,
            "recognition_confidence" : 0.1,
            "recognition_gray_scale" : True,
            "judge_default_result":True,
            "log_file_path_list":["../Log/log_test_all.log","../Log/log_test1-1.log"],
            "log_print_standard_output" : True,
            "log_function" : True,
            "log_arguments" : False,
            "step_check_mode" : True
        }
        #設定でInstance作成
        recognition=Recognition.Recognition(settings_dictionary)
        #設定を読みだす
        read_settings_dictionary = recognition.Get_SettingsDictionary()
        #読みだした設定で再度Instance作成
        recognition=Recognition.Recognition(read_settings_dictionary)
        #設定の実行
        recognition.Execute()
        
        plan_lists_dictionary={
            "test1" :
            [
                {
                    "name":"test1",
                    "type":"Log",
                    "comment":"起動開始のTaskは参照できるInfomaionが少ないので基本的にcondition無しになるかも。",
                    "step_check_mode" : True,
                    "settings" : {"message":"######Recognitionの動作確認#####","level":"WARN"}
                },
                {
                    "name":"test1-1",
                    "type":"Recognition",
                    "settings" : settings_dictionary,
                },
                {
                    "name":"test1-2",
                    "type":"Recognition",
                    "condition_list": ["Result_test1-1=True"],
                    "settings" : settings_dictionary
                }
                
            ],
            "test2" :
            [
                {
                    "name":"test2",
                    "type":"Log",
                    "step_check_mode" : True,
                    "settings" : {"message":"######PlanList、CheckDay、Judgeの動作確認#####","level":"WARN"}
                },
                {
                    "name":"test2",
                    "type":"RunPlanLists",
                    "settings" :
                    {
                        "file_path":"PlanLists.json",
                        "plan_lists":[
                            "test2-1" ,
                            "test2-2"],
                        "log_file_path_list":["../Log/log_test_all.log","../Log/log_test2.log"],
                        "log_print_standard_output" : True,
                        "step_check_mode" : True

                    }
                }
            ],
            "test2-1" :
            [
                {
                    "name":"DayCondition1",
                    "type":"CheckDay",
                    "comment":"比較する時刻に矛盾が無いことを確認する関数。Day1,Day2には特定の日付か曜日を含む時間を入れられる。day2には曜日は入れられない。day1かday3片方が曜日の場合は一週間回って必ず成立するのでTrue。",
                    "settings" : {
                        "day1" :"月曜日10:20",
                        "day2" :"Now",
                        "day3" :"水曜日22:30",
                        "log_print_standard_output" : True,
                        "log_file_path_list":"../Log/log_test_all.log"

                    }
                },
                {
                    "name":"DayCondition2",
                    "type":"CheckDay",
                    "comment":"比較する時刻に矛盾が無いことを確認する関数。Day1,Day2には特定の日付か曜日を含む時間を入れられる。day2には曜日は入れられない。day1かday3片方が曜日の場合は一週間回って必ず成立するのでTrue。",

                    "settings" : {
                        "log_print_standard_output" : True,
                        "log_file_path_list":"../Log/log_test_all.log",
                        "day1" :"水曜日22:30",
                        "day2" :"Now",
                        "day3" :"月曜日10:20"
                    }
                },
                {
                    "name":"DayCondition3",
                    "type":"CheckDay",
                    "settings" : {
                        "log_print_standard_output" : True,
                        "day1" :"木曜10:20",
                        "day2" :"2023/3/9 10:30:10",
                        "day3" :"Friday 22:30",
                        "log_file_path_list":"../Log/log_test_all.log"
                    }
                },
{
                    "name":"DayCondition4",
                    "type":"CheckDay",
                    "settings" : {
                        "log_print_standard_output" : True,
                        "day1" :"10:20",
                        "day2" :"2023/3/9 10:30:10",
                        "day3" :"10:40:23",
                        "log_file_path_list":"../Log/log_test_all.log"
                    }
                },
                {
                    "name":"Condition_Execute",
                    "type":"Judge",
                    "result_name":"Condition_Execute",
                    "settings" : {
                        "log_print_standard_output" : True,
                        "log_file_path_list":"../Log/log_test_all.log",
                        "condition_list":["Result_DayCondition1=True,Result_DayCondition2=True,Result_DayCondition3=True","Result_DayCondition3=True"]
                    }
                },
                {
                    "comment": "比較する時刻に矛盾が無いことを確認する関数。Day1,Day2には特定の日付か曜日を含む時間を入れられる。day2には曜日は入れられない。day1かday3片方が曜日の場合は一週間回って必ず成立するのでTrue。",
                    "name": "TimeCheck_1",
                    "type": "CheckDay",
                    "result_name":"Time_Check1",
                    "settings": {
                        "day1": "土曜日0:00",
                        "day2": "Now",
                        "day3": "日曜日24:00",
                        "log_file_path_list": "../Log/log_houchi.json",
                        "log_print_standard_output": True,
                        "step_check_mode" : True

                }
                },

                {
                    "name":"test2-1-1",
                    "type":"Recognition",
                    "condition_list" : ["Condition_Execute=True"],
                    "settings" : settings_dictionary,
                },
                {
                    "name":"test2-1-2",
                    "type":"Recognition",
                    "condition_list" : ["Result_DayCondition1=True,Result_DayCondition2=True"],
                    "settings" : settings_dictionary,
                },
                {
                    "name":"test2-1-3",
                    "type":"Recognition",
                    "comment":"CheckDayをconditionに入れたバージョン。符号が<=で良いかどうか微妙。",
                    "condition_list" : ["水曜日10:20<=Now<=月曜日22:30,木曜日10:20<=Now<=金曜日22:30","Result_test2-1-1=True"],
                    "settings" : settings_dictionary
                }
            ],

            "test2-2" :
            [
                {
                    "name":"test2-2-1",
                    "type":"Recognition",
                    "settings" : settings_dictionary,
                },
                {
                    "name":"test2-2-2",
                    "type":"Recognition",
                    "settings" : settings_dictionary
                }
            ]

        }
        JSON_Control.WriteDictionary("RunPlanLists_Test.json" , plan_lists_dictionary)
        task = Task.Task("RunPlanLists_Test.json")
        print("task.Run( test1, , plan_lists_dictionary)")
        task.Run( "test1","" , plan_lists_dictionary)
        print("task.Run( test2, , plan_lists_dictionary)")
        task.Run( "test2","" , plan_lists_dictionary)
        
        # def test_Auto6_Scheduler(self):
        
        #plan_list = plan_list.plan_list()
        #plan_list.ExeduteTask()
        #Scheduler.Executeplan_list("test")

#Main Program実行部
def main():


    unittest.main()

if __name__ == "__main__":
    sys.exit(main())
