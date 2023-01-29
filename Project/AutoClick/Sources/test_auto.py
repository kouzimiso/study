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

import log
import adb
import ocr
import auto
import weekday
import xml_control
import xml.dom.minidom
import image_delete
import image_control
import json_control
import FileControl
import Scheduler
import Task
import Action
import Parser


#log関係
message_list=[]
logfile_path='../Log/log_test_auto.txt'#準備必要問題:Folder

check_planlist={
	"Start": 
	[
		{
			"name" : "StartTask",
		 	"type" : "RunPlanLists",
		 	"setting" : {
				"FilePath" : "",
				"RunPlanLists" : [
					"HotSpotON",
			 		"Mementomori",
 					"Houchi",
					"ShutDown"
				]
			}
		}
	],
	"Mementomori" : 
	[
		{
			"name" : "StartTask",
			"type" : "RunPlanLists",
	 		"setting" : {
		 		"FilePath" : "",
		 		"RunPlanLists" : [
					"CloseWindow",
					"MementomoriClick01",
		 			"MementomoriClick02"
				]
			}
		}
	],
	"Houchi" : 
	[
		{
	 		"name" : "StartTask",
			"type" : "RunPlanLists",
			"setting" : {
				"FilePath" : "",
 		 		"RunPlanLists" : [
					"CloseWindow",
		 			"HouchClick01",
					"HouchClick02"
				]
			}
		}
	],

	"HotSpotON":
	[
		{
			"name" : "HotSpotON",
			"type" : "Recognition",
			"setting" : {
				"action" : "ACTION.CLICK",
				"end_condition" : "RESULT.OK",
				"end_action" : "END_ACTION.FOLDER_END_BREAK",
				"execute_number" : 2,
				"retry_number" : 2,
				"image_path" : "../Images/hotspot/*.png",
				"interval_time" : 1.8,
				"recognition_confidence" : 0.95,
				"recognition_grayscale" : True
			}
		}
	],

	"CloseWindow":
	[
		{
			"name" : "CloseWindow",
			"type" : "Recognition",
			"setting" : {
				"action" : "ACTION.CLICK",
				"end_condition" : "RESULT.OK",
				"end_action" : "END_ACTION.CONTINUE",
				"execute_number" : 2,
				"retry_number" : 2,
				"image_path" : "../Images/image_end/*.png",
				"interval_time" : 1.8,
				"recognition_confidence" : 0.95,
				"recognition_grayscale" : True
			}
		}
	],

	"MementomoriClick01":
	[
		{
			"name" : "MementomoryRun01",
			"type" : "Recognition",
			"setting" : {
				"action" : "ACTION.DOUBLE_CLICK",
				"end_condition" : "RESULT.OK",
				"end_action" : "END_ACTION.BREAK",
				"execute_number" : 1,
				"retry_number" : 3,
				"image_path" : "../Images/mementomori/Click00*.png",
				"interval_time" : 1.8,
				"recognition_confidence" : 0.95,
				"recognition_grayscale" : True
			}
		},
		{
			"name" : "MementomoryRun02",
			"type" : "Recognition",
			"condition" : ["Result.MementomoryRun01=True"],
			"setting" : {
				"action" : "ACTION.DOUBLE_CLICK",
				"end_condition" : "RESULT.NG",
				"end_action" : "END_ACTION.CONTINUE",
				"execute_number" : 25,
				"retry_number" : 100,
				"image_path" : "../Images/mementomori/Click00*.png",
				"interval_time" : 5,
				"recognition_confidence" : 0.95,
				"recognition_grayscale" : True
			}
		},
		{
			"name" : "MementomoryRun03",
			"type" : "Recognition",
			"condition" : ["Result.MementomoryRun02=True"],
			"setting" : {
				"action" : "ACTION.CLICK",
				"end_condition" : "RESULT.NG",
				"end_action" : "END_ACTION.CONTINUE",
				"execute_number" : 25,
				"retry_number" : 100,
				"image_path" : "../Images/mementomori/Click00*.png",
				"interval_time" : 5,
				"recognition_confidence" : 0.95,
				"recognition_grayscale" : True
			}
		},
		{
		 	"name" : "Information_Calc" ,
			"type" : "Information_Calc" ,
			"setting" : {
				"expression" : "Result.MementomoryRun01 + Result.MementomoryRun02 + Result.MementomoryRun03",
				"target_item_list" : [],
				"target_item_calc_list" : ["detect_rate=detect/(detect+undetect)"],
				"target_ignore_item_list" : ["total.+"]
			}
		},
		{
			"name" : "Information_Reset",
			"type" : "Information_Reset",
			"setting" : {
				"expression" : "",
				"target_item_calc_list" : ["detect_rate=detect/(detect+undetect)"],
				"target_ignore_item_list" : []
			}
		}
	],
	"HouchClick01":
	[
		{
			"name": "HouchRun01",
			"type": "Recognition",
			"setting": {
				"action": "ACTION.DOUBLE_CLICK",
				"end_condition": "RESULT.OK",
				"end_action": "END_ACTION.BREAK",
				"execute_number": 2,
				"retry_number": 0,
				"image_path": "../Images/image00/*.png",
				"interval_time": 10,
				"recognition_confidence": 0.99,
				"recognition_grayscale": True
			}
		}
	],
	"HouchClick02":
	[
		{
			"name": "HouchRun02",
			"type": "Recognition",
			"setting": {
				"action": "ACTION.DOUBLE_CLICK",
				"end_condition": "RESULT.OK",
				"end_action": "END_ACTION.BREAK",
				"execute_number": 2,
				"retry_number": 0,
				"image_path": "../Images/image02/*.png",
				"interval_time": 10,
				"recognition_confidence": 0.99,
				"recognition_grayscale": True
			}
		}
	],
	"HouchClick03":
	[
		{
			"name": "HouchRun03",
			"type": "Recognition",
			"setting": {
				"action": "ACTION.DOUBLE_CLICK",
				"end_condition": "RESULT.OK",
				"end_action": "END_ACTION.BREAK",
				"execute_number": 2,
				"retry_number": 0,
				"image_path": "../Images/image03/*.png",
				"interval_time": 10,
				"recognition_confidence": 0.99,
				"recognition_grayscale": True
			}
		}
	],
	"HouchClick04":
	[
		{
			"name": "HouchRun04",
			"type": "Recognition",
			"setting": {
				"action": "ACTION.DOUBLE_CLICK",
				"end_condition": "RESULT.OK",
				"end_action": "END_ACTION.BREAK",
				"execute_number": 2,
				"retry_number": 0,
				"image_path": "../Images/image04/*.png",
				"interval_time": 10,
				"recognition_confidence": 0.99,
				"recognition_grayscale": True
			}
		}
	],
	"HouchClick05":
	[
		{
			"name": "HouchRun05",
			"type": "Recognition",
			"setting": {
				"action": "ACTION.DOUBLE_CLICK",
				"end_condition": "RESULT.OK",
				"end_action": "END_ACTION.BREAK",
				"execute_number": 2,
				"retry_number": 0,
				"image_path": "../Images/image05/*.png",
				"interval_time": 10,
				"recognition_confidence": 0.99,
				"recognition_grayscale": True
			}
		}
	],
	"HouchClick06":
	[
		{
			"name": "HouchRun06",
			"type": "Recognition",
			"setting": {
				"action": "ACTION.DOUBLE_CLICK",
				"end_condition": "RESULT.OK",
				"end_action": "END_ACTION.BREAK",
				"execute_number": 2,
				"retry_number": 0,
				"image_path": "../Images/image06/*.png",
				"interval_time": 10,
				"recognition_confidence": 0.99,
				"recognition_grayscale": True
			}
		}
	],
	"ShutDown":
	[
		{
			"name": "ShutDown",
			"type": "ShutDown",
			"setting": {}
		}
	]	
}


class Test(unittest.TestCase):
    def test_unittest_assertEqual(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"assert命令自体のTest")
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
            
        
    def test_Auto5_dictionarytodata(self):
        recognition_information=auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 5 ,'./Test/*.png' , 1.8 , 0.8 , True)
        setting_dictionary = {
            "action" : "ACTION.CLICK" ,
            "end_condition" : "RESULT.OK",
            "execute_number" : 1,
            "retry_number" : 1,
            "end_action" : "END_ACTION.CONTINUE",
            "image_path" : "../Images/test/*.png",
            "interval_time" : 1,
            "recognition_confidence" : 0.1,
            "recognition_grayscale" : True
        }
        #設定でInstance作成
        recognition=auto.Recognition(setting_dictionary)
        #設定を読みだす
        read_setting_dictionary = recognition.Get_SettingDictionary()
        #読みだした設定で再度Instance作成
        recognition=auto.Recognition(read_setting_dictionary)
        #設定のCheck
        recognition.CheckSettingDictionary(setting_dictionary)
        recognition.CheckSettingDictionary(read_setting_dictionary)
        recognition.CheckSetting()
        #設定の実行
        recognition.Execute()
        
        plan_lists_dictionary={
            "test1" :
            [
                {
                    "name":"test1-1",
                    "type":"Recognition",
                    "comment":"起動開始のTaskは最終的には日時判断はさせても良いが、参照できるInfomaionが少ないので基本的にcondition無しになるかも。",
                    "setting" : setting_dictionary,
                },
                {
                    "name":"test1-2",
                    "type":"Recognition",
                    "condition": ["Result.test1-1=True"],
                    "setting" : setting_dictionary
                }
                
            ],
            "test2" :
            [
                {
                    "name":"test2",
                    "type":"RunPlanLists",
                    "setting" :
                    {
                        "FilePath":"PlanLists.json",
                        "RunPlanLists":[
                            "test2-1" ,
                            "test2-2"
                        ]

                    }
                }
            ],
            "test2-1" :
            [
                {
                    "name":"DayCondition1",
                    "type":"Check_Day",
                    "comment":"比較する時刻に矛盾が無いことを確認する関数。Day1,Day2には特定の日付か曜日を含む時間を入れられる。day2には曜日は入れられない。day1かday3片方が曜日の場合は一週間回って必ず成立するのでTrue。",
                    "setting" : {
                        "day1" :"月曜日10:20",
                        "day2" :"Now",
                        "day3" :"水曜日22:30"
                    }
                },
                {
                    "name":"DayCondition2",
                    "type":"Check_Day",
                    "comment":"比較する時刻に矛盾が無いことを確認する関数。Day1,Day2には特定の日付か曜日を含む時間を入れられる。day2には曜日は入れられない。day1かday3片方が曜日の場合は一週間回って必ず成立するのでTrue。",
                    "setting" : {
                        "day1" :"水曜日22:30",
                        "day2" :"Now",
                        "day3" :"月曜日10:20"
                    }
                },
                {
                    "name":"DayCondition3",
                    "type":"Check_Day",
                    "setting" : {
                        "day1" :"木曜10:20",
                        "day2" :"Now",
                        "day3" :"Friday 22:30"
                    }
                },

                {
                    "name":"test2-1-1",
                    "type":"Recognition",
                    "condition" : ["Result.DayCondition1=True,Result.DayCondition2=True"],
                    "setting" : setting_dictionary,
                },
                {
                    "name":"test2-1-2",
                    "type":"Recognition",
                    "comment":"Check_Dayをconditionに入れたバージョン。符号が<=で良いかどうか微妙。",
                    "condition" : ["水曜日10:20<=Now<=月曜日22:30,木曜日10:20<=Now<=金曜日22:30","Result.test2-1-1=True"],
                    "setting" : setting_dictionary
                }
            ],
            "test2-2" :
            [
                {
                    "name":"test2-2-1",
                    "type":"Recognition",
                    "setting" : setting_dictionary,
                },
                {
                    "name":"test2-2-2",
                    "type":"Recognition",
                    "setting" : setting_dictionary
                }
            ]

        }
        json_control.WriteDictionary("RunPlanLists_Test.json" , plan_lists_dictionary)
        json_control.WriteDictionary("PlanLists_CheckTest.json" , check_planlist)
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
    
    log.Log_MessageAdd(message_list,"Log動作test1")
    log.Log_MessageAdd(message_list,"Log動作test2")
    log.Write_MessageList(logfile_path,message_list)
    log.Clear_MessageList(message_list)
    
    unittest.main()
    
    log.Log_MessageAdd(message_list,"test3")
    log.Write_MessageList(logfile_path,message_list)

if __name__ == "__main__":
    sys.exit(main())
