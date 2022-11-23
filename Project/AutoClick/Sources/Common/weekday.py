## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import datetime
import os
import log

class DayOfTheWeek:
    message_list=[]
    def __init__(self , set_monday=0 , flag_sunday_start=False):
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
            
    def Get_DayOfTheWeek(self,date_time):
        return date_time.weekday() + self.MonDay

    def Get_DayOfTheWeek_String(self,weekday):
        offset=weekday - self.MonDay
        #2022/4/18(Mon)
        day = datetime.datetime(2022,4,18 + offset, 15, 30,20,2000)        
        return day.strftime('%A')
        
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
        day_after=self.Get_DayAfterWeekDay(date_time_time2,day_of_weekday2,flag_include_today2)
        message = "[確認日時]" + date_time.strftime ( '%Y/%m/%d(%A) %H:%M' ) 
        log.Log_MessageAdd(self.message_list,message)
        
        day_of_weekday1_string=self.Get_DayOfTheWeek_String(day_of_weekday1)
        day_of_weekday2_string=self.Get_DayOfTheWeek_String(day_of_weekday2)
        message = "[設定曜日区間]" + day_of_weekday1_string + time1.strftime ( '%H:%M' ) +"～"+ day_of_weekday2_string +time2.strftime ( '%H:%M' ) 
        log.Log_MessageAdd(self.message_list,message)     
        message = "[日時区間]" + day_before.strftime ( '%Y/%m/%d(%A) %H:%M' ) +"～"+day_after.strftime ( '%Y/%m/%d(%A) %H:%M' ) 
        log.Log_MessageAdd(self.message_list,message)     
        #前と後の時間が7日間以内ならTrue,そうでないならFaultを返す。
        time_delta = day_after - day_before
        time_delta_7day= datetime.timedelta(days=7)
        if time_delta < time_delta_7day:
            message = "[区間判定]" + str(time_delta )+"(期間内)" 
            log.Log_MessageAdd(self.message_list,message)
            return True
        else:
            message = "[区間判定]" + str(time_delta )+"(期間外)" 
            log.Log_MessageAdd(self.message_list,message)
            return False
