## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import datetime
import os
import Log
import Parser
import re

class DayOfTheWeek:
    message_list=[]
    def __init__(self , set_monday=0 , flag_sunday_start=False,settings_dictionary={}):
        self.MonDay = set_monday+0
        self.TuesDay = set_monday+1
        self.WednesDay = set_monday+2
        self.ThursDay = set_monday+3
        self.FriDay = set_monday+4
        self.SaturDay = set_monday+5
        if flag_sunday_start:
            self.SunDay = set_monday-1
        else:
            self.SunDay = set_monday+6
        self.logger = Log.Logs(settings_dictionary)

    
    def SetNowInformation(self):
        Information = {}
        Information["Now"] = datetime.datetime.now()
        Information["今"] = datetime.datetime.now()
        return Information

    def SetDayInformation(self):
        Information = {}
        if  Information.get("月曜日") != self.MonDay:
            Information["月曜日"] = self.MonDay
            Information["火曜日"] = self.TuesDay
            Information["水曜日"] = self.WednesDay
            Information["木曜日"] = self.ThursDay
            Information["金曜日"] = self.FriDay
            Information["土曜日"] = self.SaturDay
            Information["月曜"] = self.MonDay
            Information["火曜"] = self.TuesDay
            Information["水曜"] = self.WednesDay
            Information["木曜"] = self.ThursDay
            Information["金曜"] = self.FriDay
            Information["土曜"] = self.SaturDay
            Information["MonDay"] = self.MonDay
            Information["TuesDay"] = self.TuesDay
            Information["WednesDay"] = self.WednesDay
            Information["ThursDay"] = self.ThursDay
            Information["FriDay"] = self.FriDay
            Information["SaturDay"] = self.SaturDay
            Information["Monday"] = self.MonDay
            Information["Tuesday"] = self.TuesDay
            Information["Wednesday"] = self.WednesDay
            Information["Thursday"] = self.ThursDay
            Information["Friday"] = self.FriDay
            Information["Saturday"] = self.SaturDay
            
        if  Information.get("日曜日") != self.SunDay:
            Information["日曜日"] = self.SunDay
            Information["日曜"] = self.SunDay
            Information["SunDay"] = self.SunDay
            Information["Sunday"] = self.SunDay
        return Information
    
    def Get_DayOfTheWeek(self,date_time):
        return date_time.weekday() + self.MonDay
    
    def Get_DayOfTheWeek_String(self,weekday):
        offset=weekday - self.MonDay
        #2022/4/18(Mon)
        day = datetime.datetime(2022,4,18 + offset, 15, 30,20,2000)        
        return day.strftime('%A')
    
    def Get_TheWeek_Offset(self,weekday,offset):
        if self.MonDay < self.SunDay:
            startday = self.MonDay 
        else:
            startday = self.SunDay 
        lastday =startday + 6
        result_detail = weekday+offset
        if result_detail <= lastday:
            return result_detail
        else:
            return startday + result_detail % 7             
        
    def Get_DayBeforeWeekDay(self,date_time, day_of_weekday,flag_include_today = False):
        if flag_include_today == True:
            if(self.Get_DayOfTheWeek(date_time) == day_of_weekday):
                return date_time
        for number in range(1,8):
            date_time_before = date_time - datetime.timedelta(days = number )
            if(self.Get_DayOfTheWeek(date_time_before) == day_of_weekday):
                return date_time_before
        return -1
    
    def Get_DayAfterWeekDay(self,date_time, day_of_weekday,flag_include_today = False):
        if flag_include_today == True:
            if(self.Get_DayOfTheWeek(date_time) == day_of_weekday):
                return date_time
        for number in range(1,8):
            date_time_after = date_time + datetime.timedelta(days = number )
            if(self.Get_DayOfTheWeek(date_time_after) == day_of_weekday):
                return date_time_after
        return -1
    
    def CheckDay(self, settings_dictionary):
        day1 = settings_dictionary.get("day1")
        day2 = settings_dictionary.get("day2")
        day3 = settings_dictionary.get("day3")

        day_information = self.SetDayInformation()
        now_information = self.SetNowInformation()
        day1_information = self.StringToDay(day1,now_information,day_information)
        day2_information = self.StringToDay(day2,now_information,day_information)
        day3_information = self.StringToDay(day3,now_information,day_information)
        details ={"result":False,"detail":{},"error":[]}

        if day1_information["type"] == "WeekAndTime" and day2_information["type"] == "DateTime" and day3_information["type"] == "WeekAndTime":
            date_time =day2_information["date_time"]
            time1 = day1_information["time"]
            day_of_weekday1 = day1_information["day_of_weekday"]
            time2 = day3_information["time"]
            day_of_weekday2 = day3_information["day_of_weekday"]
            details["result"] = self.Check_WithinRangeDay(date_time,time1, day_of_weekday1,time2,day_of_weekday2)
        #Step:Set the result to the data.
        elif day1_information["type"] == "Time" and day2_information["type"] == "DateTime" and day3_information["type"] == "Time":
            date_time =day2_information["date_time"]
            time1 = day1_information["time"]
            time2 = day3_information["time"]
    
            details["result"] = self.Check_datetime_between(date_time,time1, time2)
        else:
            details["error"].append("This function is set incorrectly")
        return details 

    def StringToDay(self,day_string,now_information,day_information):
        parser = Parser.Parser()
        tokens = parser.SplitByDictionary(day_string,day_information)
        details = {"type":"", "day_of_weekday":"","date_time":None ,"time":None }
        for token in tokens:
            value = day_information.get(token)
            if value is not None:
                details["day_of_weekday"] = value
                details["type"] = "WeekAndTime" 
            else:
                value = now_information.get(token)
                if value is not None:
                    details["date_time"] = value
                    details["type"] = "DateTime" 
                else:
                    #date_timeはDummyの入れ物。detailsが欲しい。
                    date_time = self.StringDateTimeToDatetime(token,details)
        return details
    
    def StringDateTimeToDatetime(self,date_string,details = {}):
        try:
            # try to parse as datetime
            date_string=date_string.strip(" ")
            datetime_obj = datetime.fromisoformat(date_string)
            details["date_time"] = datetime_obj#.strftime("%Y/%m/%d %H:%M:%S")
            details["type"] = "DateTime" 
            return datetime_obj
        except ValueError:
            pass
        except:
            pass

        try:
            # try to parse as datetime with custom format
            date_format = "%Y/%m/%d %H:%M:%S"
            datetime_obj = datetime.datetime.strptime(date_string, date_format)
            details["date_time"] = datetime_obj#.strftime("%Y/%m/%d %H:%M:%S")
            details["type"] = "DateTime" 
            return datetime_obj
        except ValueError:
            pass
        except:
            pass

        try:
            # try to parse as time
            date_format = '%H:%M:%S'
            time_obj = datetime.datetime.strptime(date_string, date_format).time()
            details["time"] = time_obj#.strftime('%H:%M:%S')
            if(details.get("type","") == ""):
                details["type"] = "Time" 
            return time_obj
        except :
            pass

        try:
            # try to parse as time
            date_format = '%H:%M'
            time_obj = datetime.datetime.strptime(date_string, date_format).time()
            details["time"] = time_obj#.strftime('%H:%M:%S')
            if(details.get("type","") == ""):
                details["type"] = "Time" 
            return time_obj
        except ValueError:
            time_dictionary = parse_time(date_string)
            weekday = details.get("day_of_weekday")
            offset = time_dictionary.get("overday")
            day_of_weekday = self.Get_TheWeek_Offset(weekday,offset)
            details["day_of_weekday"] = day_of_weekday
            details["time"] =  time_dictionary.get("time")
        except :
            details["time"] = None
            details["type"] = "Error" 
            return None



    def Check_WithinRangeDay(self,date_time,time1, day_of_weekday1,time2,day_of_weekday2):
        #time1をdate_timeと同じ日のdatetime型(time1の日時)に変換する。
        date_time_time1 = datetime.datetime(date_time.year , date_time.month , date_time.day , time1.hour , time1.minute , time1.second , time1.microsecond , date_time.tzinfo)
        #time1の日時がdate_time以前なら当日含める1つ前の指定曜日を求める。
        #time1の日時がdate_timeより後なら当日含めない１つ前の指定曜日を求める。
        if date_time_time1 <=  date_time:
            flag_include_today1 = True
        else:
            flag_include_today1 = False
        day_before=self.Get_DayBeforeWeekDay(date_time_time1,day_of_weekday1,flag_include_today1)
        #同じように1つ後の指定曜日の日時を求める
        date_time_time2 = datetime.datetime(date_time.year , date_time.month , date_time.day , time2.hour , time2.minute , time2.second , time2.microsecond , date_time.tzinfo)
        if date_time <=  date_time_time2:
            flag_include_today2 = True
        else:
            flag_include_today2 = False
        details={}
        day_after=self.Get_DayAfterWeekDay(date_time_time2,day_of_weekday2,flag_include_today2)
        day_of_weekday1_string=self.Get_DayOfTheWeek_String(day_of_weekday1)
        day_of_weekday2_string=self.Get_DayOfTheWeek_String(day_of_weekday2)
        #前と後の時間が7日間以内ならTrue,そうでないならFaultを返す。
        time_delta = day_after - day_before
        time_delta_7day= datetime.timedelta(days=7)
        details["time"] = str(time_delta )
        details["check_date"] = date_time.strftime ( '%Y/%m/%d(%A) %H:%M' ) 
        details["setting_zone"] = day_of_weekday1_string + time1.strftime ( '%H:%M' ) +"～"+ day_of_weekday2_string +time2.strftime ( '%H:%M' ) 
        details["check_zone"] = day_before.strftime ( '%Y/%m/%d(%A) %H:%M' ) +"～"+day_after.strftime ( '%Y/%m/%d(%A) %H:%M' ) 
        if time_delta < time_delta_7day:
            self.logger.log("day check true","INFO",details=details)     
            return True
        else:
            self.logger.log("day check false","INFO",details=details)     
            return False
        
    def Check_datetime_between(self,check_datetime, start_time, end_time):
        """ある日のある時間のdatetimeオブジェクトが2つのtimeオブジェクトの間の時間の時にTrueを返す関数"""
        # check_datetimeから日付部分を取り出して、start_timeとend_timeのdate情報を加える
        start_datetime = datetime.datetime.combine(check_datetime.date(), start_time)
        end_datetime = datetime.datetime.combine(check_datetime.date(), end_time)

        # end_datetimeがstart_datetimeより前にある場合は、end_datetimeに1日分の時間を加算する
        if end_datetime < start_datetime:
            end_datetime += datetime.timedelta(days=1)

        # check_datetimeがstart_datetimeとend_datetimeの間にある場合にTrueを返す
        return start_datetime <= check_datetime <= end_datetime

def parse_time(string):
    time_regex = re.compile(r'(\d{2}):(\d{2}):(\d{2})')
    match = time_regex.search(string)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3))
    else:
        time_regex = re.compile(r'(\d{2}):(\d{2})')
        match = time_regex.search(string)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            second = 00
        else:
            return None
    over_day= int(hour//24)
    hour = int(hour % 24)
    time = datetime.time(hour,minute,second)
    time_dictionary = {"hour": hour, "minute": minute, "second": second,"time":time,"over_day":over_day}
    return time_dictionary
