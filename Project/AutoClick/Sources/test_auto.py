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


#log関係
message_list=[]
logfile_path='../Log/log_test_auto.txt'#準備必要問題:Folder



class Test(unittest.TestCase):
        
    def test_Auto5_dictionarytodata(self):
        recognition_information=auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 5 ,'./Test/*.png' , 1.8 , 0.8 , True)
        setting_dictionary={
            "action" : "ACTION.CLICK" ,
            "end_condition" : "RESULT.OK",
            "execute_number" : 1,
            "retry_number" : 1,
            "end_action" : "END_ACTION.CONTINUE",
            "image_path" : "../Images/test/*.png",
            "interval_time" : 1,
            "recognition_confidence" : 0.1,
            "recognition_grayscale" : 0.8
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
                    "setting" : setting_dictionary,
                },
                {
                    "name":"test1-2",
                    "type":"Recognition",
                    "setting" : setting_dictionary
                }
            ],
            "test2" :
            [
                {
                    "name":"test2",
                    "type":"RunPlanLists",
                    "condition": ["水曜日10:20～月曜日22:30 or 木曜日10:20～金曜日22:30","test1-1=True or test1-2=True"],
                    "setting" :
                    {
                        "RunPlanLists":[
                            "test2-1",
                            "test2-2"
                        ]

                    }
                }
            ],
            "test2-1" :
            [
                {
                    "name":"test2-1-1",
                    "type":"Recognition",
                    "setting" : setting_dictionary,
                },
                {
                    "name":"test2-1-2",
                    "type":"Recognition",
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
            ],

        
        }
        
        task = Task.Task()
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
