## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import sys
import os
import datetime
import cv2
import json
#import clr
import PIL
import unittest
import socket
import threading
import dataclasses
import difflib
import logging
import xml.dom.minidom
import os

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
import ImageDelete
import FileControl
import ImageControl


#log関係
message_list=[]
logfile_path='../Log/log_test_auto.txt'#準備必要問題:Folder

@dataclasses.dataclass
class testdata_class:
    data_string:str
    data_int:int
    data_float:float

class Test(unittest.TestCase):

    def test_unittest_assertEqual(self):
        if os.path.isfile ("../Log/test1.txt"):
            os.remove("../Log/test1.txt")
        if os.path.isfile ("../Log/test2.txt"):
            os.remove("../Log/test2.txt")
        #機能の名称を取得
        function_name=sys._getframe().f_code.co_name
        #Messageを追加する
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"Test")
        logs = Log.Logs()
        logs.Message_Add("../Log/test1.txt","["+function_name+"]"+"Test1-1")
        logs.Message_Add("../Log/test2.txt","["+function_name+"]"+"Test2-1")
        #MessageをFileに書込む
        logs.MessageList_Write("../Log/test1.txt")
        logs.MessageList_Write("../Log/test2.txt")
        logs.MessageList_Clear("../Log/test2.txt")
        logs.MessageList_Write(["../Log/test1.txt","../Log/test2.txt"])
        logs.MessageList_Clear(["../Log/test1.txt","../Log/test2.txt"])
        logs.Message_Add(["../Log/test1.txt","../Log/test2.txt"],"["+function_name+"]"+"Test1とTest2両方書き込み")
        logs.MessageList_Write("../Log/test1.txt")
        logs.MessageList_Write("../Log/test2.txt")

        #current_work_directory=os.getcwd
        file_path1 = os.path.abspath("../Log/test1.txt")
        file_path2 = os.path.abspath("../Log/test2.txt")
        os.startfile(file_path1)
        os.startfile(file_path2)
        
        file1 = open(file_path1)
        file2 = open(file_path2)
        diff = difflib.Differ()
        result_detail = diff.compare(file1.readlines(),file2.readlines())
        for data in result_detail :
            if data[0:1] in ['+', '-'] :
                print(data)   
        file1.close()
        file2.close()

        print("test")
        json_read = JSON_Control.ReadDictionary("..\conf\conf.json")
        print(json_read)
        
        num=3
        expected =6
        actual=2*num
        self.assertEqual(expected,actual)

    def test_log(self):
        custom_logger = logging.getLogger('custom_logger')
        custom_logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler() # ハンドラーを作成
        handler.setLevel(logging.DEBUG) # ハンドラーのログレベルを設定
        custom_logger.addHandler(handler) # カスタムロガーにハンドラーを紐づける

        custom_logger.warning('Watch out!')
        custom_logger.info('I told you so')
        print(custom_logger.handlers)
        
        logger = logging.basicConfig(level=logging.DEBUG)
        logger.warning("warning log")
        logger.info("info log")
        rows=10
        logger.info('info log+dictionary',extra={'rows':rows})


    def test_for(self):
        string_list=["a","b","c"]
        print("pythonではfor *** in ***文でListでもstring単体でも回せる")
        for text in string_list:
            print("List:" + text)
            for text2 in text:
                print( "String単体:" + text2)
        
    def test_ADB(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"ADBのTest")
        device_address = ADB.Get_DeviceAddress()
        screen_size = ADB.Get_ScreenSize(device_address)
        Log.Log_MessageAdd(message_list,str(screen_size))
        ADB.ScreenCapture(device_address,"../Images/Test/screen1.png")#準備必要問題:Folder

    def test_image_delete_duplicate(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]")
        ImageControl.DeleteDuplicateImage("../Images/Test")#準備必要問題:Folder

    def test_OCR(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"OCRのTest")
        
        #画面Captureの文字認識
        ocr_instance = OCR.OCR()
        file_path="../Images/Test/screen_capture_PC.png"    #準備必要問題:Folder
        PIL.ImageGrab.grab().save(file_path)
        text=ocr_instance.Recognition_ByFilePath(file_path,"jpn")
        Log.Log_MessageAdd(message_list,"ocr1:\n"+text)

        #画像処理後の文字認識       
        file_path="../Images/Test/screen_capture_PC.png"    #準備必要問題:Folder
        image = cv2.imread(file_path,0)
        image = cv2.GaussianBlur(image, (3, 3), 0)
        file_path="../Images/Test/screen_capture_PC_Blur.png"   #準備必要問題:Folder
        cv2.imwrite(file_path,image)
        ret, image = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU)
        file_path="../Images/Test/screen_capture_threshold.png" #準備必要問題:Folder
        cv2.imwrite(file_path,image)
        ocr_instance.Setting_BuilderText(6)
        text=ocr_instance.Recognition_ByFilePath(file_path,"jpn")
        Log.Log_MessageAdd(message_list,"{ocr2:"+text+"}\n")

        
    def test_WeekDay0001(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest")

        day=datetime.datetime(2022,4,18, 15, 30,20,2000)
        
        week_day=Weekday.DayOfTheWeek()
        
        expected=week_day.MonDay
        actual=week_day.Get_DayOfTheWeek(day)
        Log.Log_MessageAdd(message_list,week_day.Get_DayOfTheWeek_String(actual))
        self.assertEqual(expected,actual)

    def test_WeekDay0002(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest")

        #2022/4/18(Mon)
        day=datetime.datetime(2022,4,18, 15, 30,20,2000)
        
        week_day=Weekday.DayOfTheWeek(1,True)
        
        expected=week_day.MonDay
        actual=week_day.Get_DayOfTheWeek(day)
        self.assertEqual(expected,actual)
        
    def test_WeekDay0003(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:1つ前の月曜日")

        #2022/4/18(Mon)
        day = datetime.datetime(2022,4,18, 15, 30,20,2000)
        
        week_day = Weekday.DayOfTheWeek(set_monday = 1 , flag_sunday_start= True)
        day_before_monday = week_day.Get_DayBeforeWeekDay(date_time = day,day_of_weekday=week_day.MonDay,flag_include_today=False)
        message_list.extend(week_day.message_list)
        week_day.message_list.clear()
        
        expected=week_day.MonDay
        actual=week_day.Get_DayOfTheWeek(day_before_monday)
        self.assertEqual(expected,actual)

    def test_WeekDay0004(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:指定時間の間に入っているか？")

        week_day = Weekday.DayOfTheWeek(set_monday=1)
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
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:当日の12:00～23時の指定時間の間に入っているか？")

        week_day = Weekday.DayOfTheWeek(set_monday=1)
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
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:同じ曜日の23時～12:00の指定時間の間に入っているか？")

        week_day = Weekday.DayOfTheWeek(set_monday=1)
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
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"WeekDayのTest:同じ曜日の23時～12:00の指定時間の間に入っているか？")
        week_day = Weekday.DayOfTheWeek(set_monday=1)
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
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"放置少女の指定時間チェック")

        week_day = Weekday.DayOfTheWeek(set_monday=1)
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
        Log.Write_MessageList(logfile_path,message_list)

    def test_xml(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]"+"xmlのテスト")
        
        information1 = {"key1":"value1","key2":"value2","key3":"value3"}
        XML_Control.Dictionary_XMLWrite("./test.xml",information1)        
        #information1で書いたxmlを読んだのがinformation2とする
        information2 = {}
        information2 = XML_Control.XML_Read("./test.xml")
        Log.Log_MessageAdd(message_list,"Information2")
        dictionary_string = json.dumps(information2)
        Log.Log_MessageAdd(message_list,dictionary_string)
        
        print("[test_xml02]")
        
        XML_Control.Dictionary_ToXMLFile("./test2.xml",information1)
        information3 = {}
        information3 = XML_Control.XML_ToDictionary("./test2.xml")
        Log.Log_MessageAdd(message_list,"Information3")
        dictionary_string = json.dumps(information3)
        Log.Log_MessageAdd(message_list,dictionary_string)
        
        print("[test_xml03]")
        
        dictionary_string = json.dumps(information1)
        print("information1" + dictionary_string)
        expected = information1["key1"]
        
        dictionary_string = json.dumps(information2)
        print("information2" + dictionary_string)
        actual =information2["Element"]
        
        dictionary_string = json.dumps(information3)
        print("information3" + dictionary_string)
        actual = information3["root"]["key1"]
        self.assertEqual(expected,actual)

        
    def test_dataclass(self):
        data_class=testdata_class("123",123,1.23)
        data_dictionary=dataclasses.asdict(data_class)
        print(data_dictionary)

    def test_json(self):
        function_name=sys._getframe().f_code.co_name
        Log.Log_MessageAdd(message_list,"["+function_name+"]")

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
            "Function_RecognitionInformation_Setting":
            {
                "definition":{
                    "type":"function_settings",
                    "type_deteil":"RecognitionInformation",
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
                        "recognition_gray_scale":"True"
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
                        "recognition_gray_scale":"True"
                    }

                }
            }
 
        }
                                    

        """
        search_sequence=[]
        search_sequence.append(Auto.RecognitionInformation(Auto.ACTION.DOUBLE_CLICK ,Auto.RESULT.OK, Auto.END_ACTION.BREAK , 2 , 0 ,'./image00/*.png' , 10 , 0.99 , True))
        search_sequence.append(Auto.RecognitionInformation(Auto.ACTION.DOUBLE_CLICK ,Auto.RESULT.OK, Auto.END_ACTION.BREAK , 2 , 0 ,'./image01/*.png' , 10 , 0.97 , True))
        search_sequence.append(Auto.RecognitionInformation(Auto.ACTION.DOUBLE_CLICK ,Auto.RESULT.OK, Auto.END_ACTION.BREAK , 2 , 0 ,'./image02/*.png' , 10 , 0.99 , True))
        search_sequence.append(Auto.RecognitionInformation(Auto.ACTION.DOUBLE_CLICK ,Auto.RESULT.OK, Auto.END_ACTION.BREAK , 2 , 0 ,'./image03/*.png' , 10 , 0.99 , True))
        search_sequence.append(Auto.RecognitionInformation(Auto.ACTION.DOUBLE_CLICK ,Auto.RESULT.OK, Auto.END_ACTION.BREAK , 2 , 0 ,'./image04/*.png' , 10 , 0.99 , True))
        search_sequence.append(Auto.RecognitionInformation(Auto.ACTION.DOUBLE_CLICK ,Auto.RESULT.OK, Auto.END_ACTION.BREAK , 2 , 0 ,'./image05/*.png' , 10 , 0.99 , True))
        information1 = search_sequence
        """

        file_path = "test.json"
        file = open(file_path,'w', encoding='utf-8')
        json.dump(information1,file,ensure_ascii = False,indent=4,separators=(',',':'))        
        file.close()

        information1 = {"file_path1":{"detect":1,"undetect":2},"file_path":{"detect":1,"undetect":2}}        
        JSON_Control.WriteDictionary("test2.json",information1)
        JSON_Control.ReadDictionary("test2.json",information1)
        print(information1)


    def text_xml2(self):
        xml_text="<?xml version='1.0' encoding='utf-8'?><root><Element><key>value1</key><value>value1</value><key>value2</key><value>value2</value><key>value3</key><value>value3</value></Element></root>"
        xml_document = xml.dom.minidom.parseString(xml_text.encode("utf-8"))

        print("[test_xml04]")
        print(xml_document)
        XML_Control.XML_Write("./text_xml_write.xml",xml_document)

    def test_rate(self):
        expected=0.1
        actual=Auto.rate(1,2,3,4)
        self.assertEqual(expected,actual)

        expected=0
        actual=Auto.rate(1,-1)
        self.assertEqual(expected,actual)



    def test_Auto1(self):
        print("####test_Auto1####")
        Auto.Image_AroundPoint("../Images/Test/Image_Screen.png")
        Auto.Image_AroundPoint("../Images/Test/Image_PIL_capture.png",True,0,0,100,200)
        Auto.Image_AroundMouse("../Images/Test/Image_mouse_capture.png",False,200,100,"{}_{:0=3}{}")
 
    def test_Auto2_ConditionCheck(self):
        print("####test_Auto2_ConditionCheck####")
        file_path='../Images/Test/Image_mouse_capture.png'
        ImageControl.Image_AroundMouse(file_path, flag_overwrite=True, wide=100, height=100)
        image_instance = ImageControl.open(file_path)
        image_instance.show()
        x,y=Auto.Image_SearchAndXY(file_path , True , 0.5)
        Log.Log_MessageAdd(message_list,"test_Images_ConditionCheckAndAction x" + str(x) + "y:" + str(y))

    def test_Auto3_ConditionCheckAndAction(self):
        print("####test_Auto3_ConditionCheckAndAction####")
        #アニメーションするボタンが押せない対策
        #画像を探してずらした位置をクリックする設定。{画像Path:ずらす位置}の形式で記述する。
        x_offset_dictionary= {'../Images/Test/test_Auto_Blank' : "0"}
        y_offset_dictionary= {'../Images/Test/test_Auto_Blank' : "30"}
        Auto.Images_Action_Result=Auto.ReadInformationFromJson("../Log/test_auto.json")
        Auto.Images_Action_Result=Auto.Images_Action_ResultInit(Auto.Images_Action_Result)
        
        recognition_information=Auto.RecognitionInformation(Auto.ACTION.DOUBLE_CLICK ,Auto.RESULT.OK, Auto.END_ACTION.BREAK , 2 , 5 ,'./Test/*.png' , 1.8 , 0.8 , True)
        actual=Auto.Images_ConditionCheckAndAction("test1",Auto.RESULT.OK,recognition_information,x_offset_dictionary,y_offset_dictionary)
        Auto.WriteInformationToJson("../Log/test_auto.json")
        
        print("test_Auto3_ConditionCheckAndAction1")
        expected =Auto.RESULT.ALL_OK
        #self.assertEqual(expected,actual)
        print(Auto.InformationToString())

        actual=Auto.Images_ConditionCheckAndAction("test1",Auto.RESULT.OK,recognition_information,x_offset_dictionary,y_offset_dictionary)
        expected =Auto.RESULT.NG
        #self.assertEqual(expected,actual)

        print("test_Auto3_ConditionCheckAndAction2")

        actual=Auto.Images_ConditionCheckAndAction("test1",Auto.RESULT.NG,recognition_information,x_offset_dictionary,y_offset_dictionary)
        expected =Auto.RESULT.NG
        #self.assertEqual(expected,actual)
        print("test_Auto3_ConditionCheckAndAction3")
        Auto.WriteInformationToJson("../Log/test_auto.json")      
        
    def test_Auto4_FileControl(self):
        folder_path="../Images/Test"
        folder_maxsize=1000
        files_maxnumber=10
        FileControl.Delete_OldFiles(folder_path,  folder_maxsize , files_maxnumber)


    def test_pythonnet(self):
        print(".netのdll読込")

        #clr.AddReference('../Reference/FileControl')
        clr.AddReference('FileControl')
        from Commons import ControlFile

        control_file = ControlFile()
        control_file.DeleteOldFile("../Log/",5)

        thread_windows_form = FormWindows()
        thread_windows_form.start()
        print('thread_windows_form started')
        #thread_windows_form.join()
        #print('thread_windows_form finished')
  
    def test_get_PC_name(self):

        # ホスト名を取得
        host = socket.gethostname()
        print(host)
        
class FormWindows(threading.Thread):
    def run(self):
        print("Windows.Form動作確認")
        clr.AddReference('System.Windows.Forms')
        from System.Windows.Forms import Application,Form

        Application.EnableVisualStyles()
        Application.SetCompatibleTextRenderingDefault(False)
        Application.Run(Form())

#Main Program実行部
def main():

    Log.Log_MessageAdd(message_list,"Log動作test1")
    Log.Log_MessageAdd(message_list,"Log動作test2")
    Log.Write_MessageList(logfile_path,message_list)
    Log.Clear_MessageList(message_list)
    
    unittest.main()

    Log.Log_MessageAdd(message_list,"test3")
    Log.Write_MessageList(logfile_path,message_list)

if __name__ == "__main__":
    sys.exit(main())
