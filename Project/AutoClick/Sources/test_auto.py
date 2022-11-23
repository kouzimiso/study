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
import json_control

#log関係
message_list=[]
logfile_path='../Log/log_test_auto.txt'

class Test(unittest.TestCase):

    def test_unittest_assertEqual(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"assert命令自体のTest")
        num=3
        expected =6
        actual=2*num
        self.assertEqual(expected,actual)


    def test_adb(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"adbのTest")
        device_address = adb.Get_DeviceAddress()
        screen_size = adb.Get_ScreenSize(device_address)
        log.Log_MessageAdd(message_list,str(screen_size))
        adb.ScreenCapture(device_address,"../Images/Test/screen1.png")

    def test_image_delete_duplicate(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]")
        image_delete.Image_DeleteDuplicate("../Images/Test")

    def test_OCR(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"OCRのTest")
        
        #画面Captureの文字認識
        ocr_instance = ocr.OCR()
        file_path="../Images/Test/screen_capture_PC.png"
        PIL.ImageGrab.grab().save(file_path)
        text=ocr_instance.Recognition_ByFilePath(file_path,"jpn")
        log.Log_MessageAdd(message_list,"ocr1:\n"+text)

        #画像処理後の文字認識       
        file_path="../Images/Test/screen_capture_PC.png"
        image = cv2.imread(file_path,0)
        image = cv2.GaussianBlur(image, (3, 3), 0)
        file_path="../Images/Test/screen_capture_PC_Blur.png"
        cv2.imwrite(file_path,image)
        ret, image = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU)
        file_path="../Images/Test/screen_capture_threshold.png"
        cv2.imwrite(file_path,image)
        ocr_instance.Setting_BuilderText(6)
        text=ocr_instance.Recognition_ByFilePath(file_path,"jpn")
        log.Log_MessageAdd(message_list,"{ocr2:"+text+"}\n")

        #指定画像の文字認識
        file_path="../Images/Test/test_OCR_Houch.png"
        text=ocr_instance.Recognition_ByFilePath(file_path,"jpn")
        log.Log_MessageAdd(message_list,"{ocr3:"+text+"}\n")

        
    def test_WeekDay0001(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest")

        day=datetime.datetime(2022,4,18, 15, 30,20,2000)
        
        week_day=weekday.DayOfTheWeek()
        
        expected=week_day.MonDay
        actual=week_day.Get_DayOfTheWeek(day)
        log.Log_MessageAdd(message_list,week_day.Get_DayOfTheWeek_String(actual))
        self.assertEqual(expected,actual)

    def test_WeekDay0002(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest")

        #2022/4/18(Mon)
        day=datetime.datetime(2022,4,18, 15, 30,20,2000)
        
        week_day=weekday.DayOfTheWeek(1,True)
        
        expected=week_day.MonDay
        actual=week_day.Get_DayOfTheWeek(day)
        self.assertEqual(expected,actual)
        
    def test_WeekDay0003(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:1つ前の月曜日")

        #2022/4/18(Mon)
        day = datetime.datetime(2022,4,18, 15, 30,20,2000)
        
        week_day = weekday.DayOfTheWeek(set_monday = 1 , flag_sunday_start= True)
        day_before_monday = week_day.Get_DayBeforeWeekDay(date_time = day,day_of_weekday=week_day.MonDay,flag_include_today=False)
        message_list.extend(week_day.message_list)
        week_day.message_list.clear()
        
        expected=week_day.MonDay
        actual=week_day.Get_DayOfTheWeek(day_before_monday)
        self.assertEqual(expected,actual)

    def test_WeekDay0004(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:指定時間の間に入っているか？")

        week_day = weekday.DayOfTheWeek(set_monday=1)
        #2022/4/18(Mon)
        date_time = datetime.datetime(2022,4,18, 15, 30,20,2000)
        time1 = datetime.time(12,00,00)
        day_of_weekday1=week_day.FriDay
        time2 = datetime.time(23,40,00)
        day_of_weekday2=week_day.SunDay
        
        expected=False
        actual=week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
        message_list.extend(week_day.message_list)
        week_day.message_list.clear()

        self.assertEqual(expected,actual)

    def test_WeekDay0005(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:当日の12:00～23時の指定時間の間に入っているか？")

        week_day = weekday.DayOfTheWeek(set_monday=1)
        #2022/4/18(Mon)
        date_time = datetime.datetime(2022,4,18, 15, 30,20,2000)
        time1 = datetime.time(12,00,00)
        day_of_weekday1=week_day.MonDay
        time2 = datetime.time(23,00,00)
        day_of_weekday2=week_day.MonDay
        message_list.extend(week_day.message_list)
        expected=True
        actual=week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
        message_list.extend(week_day.message_list)
        week_day.message_list.clear()

        self.assertEqual(expected,actual)

    def test_WeekDay0006(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:同じ曜日の23時～12:00の指定時間の間に入っているか？")

        week_day = weekday.DayOfTheWeek(set_monday=1)
        #2022/4/18(Mon)
        date_time = datetime.datetime(2022,4,18,10, 30,20,2000)
        #date_time = datetime.datetime.now()
        time1 = datetime.time(23,00,00)
        day_of_weekday1=week_day.MonDay
        time2 = datetime.time(12,00,00)
        day_of_weekday2=week_day.MonDay
        
        expected=True
        actual=week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
        self.assertEqual(expected,actual)

    def test_WeekDay0007(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:同じ曜日の23時～12:00の指定時間の間に入っているか？")
        week_day = weekday.DayOfTheWeek(set_monday=1)
        #2022/4/18(Mon)
        date_time = datetime.datetime(2022,4,18,23, 30,20,2000)
        time1 = datetime.time(23,00,00)
        day_of_weekday1=week_day.MonDay
        time2 = datetime.time(12,00,00)
        day_of_weekday2=week_day.MonDay
        
        expected=True
        actual=week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)
        self.assertEqual(expected,actual)

    def test_WeekDay0008(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"放置少女の指定時間チェック")

        week_day = weekday.DayOfTheWeek(set_monday=1)
        #2022/4/18(Mon)
        date_time = datetime.datetime(2022,4,18,12, 30,20,2000)
        #date_time = datetime.datetime.now()
        time1 = datetime.time(12,00,00)
        day_of_weekday1=week_day.FriDay
        time2 = datetime.time(23,40,00)
        day_of_weekday2=week_day.SunDay
        check1 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)

        time1 = datetime.time(12,00,00)
        day_of_weekday1=week_day.MonDay
        time2 = datetime.time(23,00,00)
        day_of_weekday2=week_day.MonDay
        check2 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)

        time1 = datetime.time(12,00,00)
        day_of_weekday1=week_day.TuesDay
        time2 = datetime.time(23,00,00)
        day_of_weekday2=week_day.WednesDay
        check3 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)

        time1 = datetime.time(12,00,00)
        day_of_weekday1=week_day.ThursDay
        time2 = datetime.time(23,00,00)
        day_of_weekday2=week_day.ThursDay
        check4 = week_day.Check_WithinRangeDay(date_time , time1, day_of_weekday1 , time2 , day_of_weekday2)

        actual = check1 or check2  or check3  or check4
        
        expected=True
        self.assertEqual(expected,actual)
        log.Write_MessageList(logfile_path,message_list)

    def test_json(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]")

        #information1 = {"key1":"value1","key2":"value2","key3":"value3"}
        information1={
            
                "port1_specification":
                {
                    "wafer_size":"300mm",
                    "pod_type":"open_cassette",
                    "slot_number":"13",
                    "maker":"Rorze",
                    "product_type":"RE116-303"
                },
            
                "port2_specification":
                {
                    "wafer_size":"200mm",
                    "pod_type":"open_cassette",
                    "slot_number":"25",
                    "maker":"Rorze",
                    "product_type":"RE116-303"
                }
                
        }
        #動作設定
        #Data種類→Data名前

        information_sequence={
            "Function_RecognitionInfomation_Setting":
            {
                "definition":{
                    "type":"function_setting",
                    "type_deteil":"RecognitionInfomation",
                },
                
                "setting":
                {
                    "search_sequence":
                    {
                        "name":"Recognition_Search",
                        "action":"DOUBLE_CLICK",
                        "end_condition":"OK",
                        "end_action":"BREAK",
                        "execute_number":"2",
                        "retry_number":"0" ,
                        "image_path":'./image00/*.png' ,
                        "interval_time":"10" ,
                        "recognition_confidence":"0.99" ,
                        "recognition_grayscale":"True"
                    },
                    "search_sequence2":
                    {
                        "name":"Recognition_Search",
                        "action":"DOUBLE_CLICK",
                        "end_condition":"OK",
                        "end_action":"BREAK",
                        "execute_number":"2",
                        "retry_number":"0" ,
                        "image_path":'./image00/*.png' ,
                        "interval_time":"10" ,
                        "recognition_confidence":"0.99" ,
                        "recognition_grayscale":"True"
                    }

                }
            }
 
        }
                                    

        """
        search_sequence=[]
        search_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 0 ,'./image00/*.png' , 10 , 0.99 , True))
        search_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 0 ,'./image01/*.png' , 10 , 0.97 , True))
        search_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 0 ,'./image02/*.png' , 10 , 0.99 , True))
        search_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 0 ,'./image03/*.png' , 10 , 0.99 , True))
        search_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 0 ,'./image04/*.png' , 10 , 0.99 , True))
        search_sequence.append(auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 0 ,'./image05/*.png' , 10 , 0.99 , True))
        information1 = search_sequence
        """

        file_path = "test.json"
        file = open(file_path,'w', encoding='utf-8')
        json.dump(information1,file,ensure_ascii = False,indent=4,separators=(',',':'))        
        file.close()

        information1 = {"file_path1":{"detect":1,"undetect":2},"file_path":{"detect":1,"undetect":2}}        
        json_control.WriteDictionary("test2.json",information1)
        json_control.ReadDictionary("test2.json",information1)
        print(information1)

        
    def test_xml(self):
        function_name=sys._getframe().f_code.co_name
        log.Log_MessageAdd(message_list,"["+function_name+"]"+"xmlのテスト")

        information1 = {"key1":"value1","key2":"value2","key3":"value3"}
        xml_control.Dictionary_XMLWrite("./test.xml",information1)        
                
        information2 = {}
        information2 = xml_control.XML_Read("./test.xml")
        log.Log_MessageAdd(message_list,"Infomation2")
        dictionary_string = json.dumps(information2)
        log.Log_MessageAdd(message_list,dictionary_string)

        print("[test_xml02]")

        xml_control.Dictionary_ToXMLFile("./test2.xml",information1)
        information3 = {}
        information3 = xml_control.XML_ToDictionary("./test2.xml")
        log.Log_MessageAdd(message_list,"Infomation3")
        dictionary_string = json.dumps(information3)
        log.Log_MessageAdd(message_list,dictionary_string)

        print("[test_xml03]")
        
        dictionary_string = json.dumps(information1)
        print("information1" + dictionary_string)
        expected = information1["key1"]

        dictionary_string = json.dumps(information2)
        print("information2" + dictionary_string)
        actual = information2["Element"]["key2"]

        dictionary_string = json.dumps(information3)
        print("information3" + dictionary_string)
        actual = information3["root"]["key1"]
        self.assertEqual(expected,actual)

    def text_xml2(self):
        xml_text="<?xml version='1.0' encoding='utf-8'?><root><Element><key>value1</key><value>value1</value><key>value2</key><value>value2</value><key>value3</key><value>value3</value></Element></root>"
        xml_document = xml.dom.minidom.parseString(xml_text.encode("utf-8"))

        print("[test_xml04]")
        print(xml_document)
        xml_control.XML_Write("./text_xml_write.xml",xml_document)

    def test_Auto1(self):
        auto.Image_AroundPoint("../Images/Test/Image_Screen.png")
        auto.Image_AroundPoint("../Images/Test/Image_PIL_capture.png",True,0,0,100,200)
        auto.Image_AroundMouse("../Images/Test/Image_mouse_capture.png",False,200,100,"{}_{:0=3}{}")
 
    def test_Auto2_ConditionCheck(self):
        x,y=auto.Image_SearchAndXY('../Images/Test/test_Auto_Blank.png' , True , 0.5)
        log.Log_MessageAdd(message_list,"test_Images_ConditionCheckAndAction x" + str(x) + "y:" + str(y))
        
    def test_Auto3_ConditionCheckAndAction(self):
        #アニメーションするボタンが押せない対策
        #画像を探してずらした位置をクリックする設定。{画像Path:ずらす位置}の形式で記述する。
        x_offset_dictionary= {'../Images/Test/test_Auto_Blank' : "0"}
        y_offset_dictionary= {'../Images/Test/test_Auto_Blank' : "30"}
        recognition_information=auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 5 ,'./Test/*.png' , 1.8 , 0.8 , True)
        actual=auto.Images_ConditionCheckAndAction("test1",auto.RESULT.OK,recognition_information,x_offset_dictionary,y_offset_dictionary)
        auto.WriteInfomationToJson("test3.json")
        
        expected =auto.RESULT.ALL_OK
        self.assertEqual(expected,actual)

        actual=auto.Images_ConditionCheckAndAction("test1",auto.RESULT.ALL_OK,recognition_information,x_offset_dictionary,y_offset_dictionary)
        expected =auto.RESULT.NG
        self.assertEqual(expected,actual)


        actual=auto.Images_ConditionCheckAndAction("test1",auto.RESULT.NG,recognition_information,x_offset_dictionary,y_offset_dictionary)
        expected =auto.RESULT.NG
        self.assertEqual(expected,actual)

    def test_Auto4_dictionarytodata(self):
        recognition_information=auto.RecognitionInfomation(auto.ACTION.DOUBLE_CLICK ,auto.RESULT.OK, auto.END_ACTION.BREAK , 2 , 5 ,'./Test/*.png' , 1.8 , 0.8 , True)
        setting_dictionary = recognition_information.get_setting_dictionary
        recognition_information.set_setting_dictionary(setting_dictionary)

    def test_pythonnet(self):

        #clr.AddReference('../Reference/FileControl')
        clr.AddReference('FileControl')
        from Commons import ControlFile

        control_file = ControlFile()
        control_file.DeleteOldFile("../Log/",5)

        clr.AddReference('System.Windows.Forms')
        from System.Windows.Forms import Application,Form

        Application.EnableVisualStyles()
        Application.SetCompatibleTextRenderingDefault(False)
        Application.Run(Form())
  
    def test_get_PC_name(self):

        # ホスト名を取得
        host = socket.gethostname()
        print(host)    

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
