## $python ##
import datetime
import os
import sys
import inspect
#from logging import getLogger , DEBUG , NullHandler
from json_log_formatter import JSONFormatter
import logging
import logging.config
import json
from pythonjsonlogger import jsonlogger


import FileControl


#class END_ACTION(Enum):
#    BREAK = 0
#    FOLDER_END_BREAK = 1
#    CONTINUE = 2

#JSONの設定Fileを読込み、Fileがない場合はDefault設定をPythonのLogging Classに設定する。
#LogはLog_append関数で現在の時間とメッセージとレベルを辞書形式でListに加えて貯める。
#Log_append関数で貯めたLogをlog_write関数でloggingのレベルでフィルタリングし、1回のFile書き込みで複数のLogをまとめてJSON.Line形式でFileに追記する
class Logs:
    Log_Lists : list = []
    Setting:dict = {}
    default_log_console_level = "WARNING"
    #MESSAGE_FORMAT ="%(asctime)s %(levelname)s %(message)s"
    MESSAGE_FORMAT ="%(message)s"
    TIME_FORMAT = "%Y/%m/%d %H:%M:%S"
    FilePathList = ["../Log/log.json"]
    DEFAULT_FORMATTER = {
        #'()' : 'pythonjsonlogger.jsonlogger.JsonFormatter' , 
        "format" : MESSAGE_FORMAT , 
        "datefmt" : TIME_FORMAT , 
        "json_default" : json.JSONEncoder.default , 
    }
    CONSOLE_HANDLER = {
        "class" : "logging.StreamHandler" , 
        "formatter" : "json" , 
        "level" : "INFO"
    }
    FILE_HANDLERS = {
        "file" : { 
            "class" : "logging.FileHandler" , 
            "filename" : "../Log/log2.json" , 
            "formatter" : "json"
        },
        "console":CONSOLE_HANDLER
    }
    
    # デフォルトのログ設定
    DEFAULT_LOGGING_CONFIG = {
        "version" : 1 , 
        "disable_existing_loggers" : False , 
        "handlers" : FILE_HANDLERS , 
        "formatters" : {
            "json" : DEFAULT_FORMATTER
        } , 
        "loggers" : {
            "files" : {
               "handlers" : ["file"] , 
                "level" : "INFO"
            } , 
            "default" : {
               "handlers" : ["file"] , 
                "level" : "INFO"
            },
            "console" : {
                "handlers" : ["console"] , 
                "level" : "INFO"
            } 

        }
    }
    
    
    def __init__(self , setting_dictionary = {}):
        self.Setup(setting_dictionary)
        
    def Setup(self , setting_dictionary = {}):
        if type(setting_dictionary) is not dict:
            setting_dictionary = {}
        self.Setting = setting_dictionary
        log_setting_path = setting_dictionary.get("log_setting_path")
        
        # ログ設定ファイルの読み込み
        try:
            if log_setting_path is None:
                config = self.DEFAULT_LOGGING_CONFIG
            else:
                with open(log_setting_path , 'rt') as f:
                    config = json.load(f)
        #except FileNotFoundError:
        except:
            with open("setting_log.json" , 'wt') as f:
                json.dump(self.DEFAULT_LOGGING_CONFIG , f , indent=4)
            config = self.DEFAULT_LOGGING_CONFIG
        logging.config.dictConfig(config)
        self.logger = logging.getLogger("file")

        self.logger_console = logging.getLogger("console")
        log_console_level = setting_dictionary.get("log_console_level",None)
        if log_console_level is not None:
            self.logger_console.setLevel(log_console_level)
        if not self.logger_console.handlers:
            handler = logging.StreamHandler(sys.stdout)
            self.logger_console.addHandler(handler)

    def debug(self , message) :
        self.log(message , "DEBUG")
        self.MessageList_Write()
        self.MessageList_Clear()

    def info(self , message) :
        self.log(message , "INFO")
        self.MessageList_Write()
        self.MessageList_Clear()
    
    def warning(self , message) :
        self.log(message , "WARNING")
        self.MessageList_Write()
        self.MessageList_Clear()

    def error(self , message,details={}) :
        error_information = get_error_dictionary()
        details.update(error_information)
        self.log(message , "ERROR" , details)
        self.MessageList_Write()
        self.MessageList_Clear()


    def Set(self , log_lists) :
        self.Log_Lists = log_lists

    def Get(self) :
        return self.Log_Lists

    def Log_Level_Get(self , log_level_string , default_log_level=logging.WARNING):
        try:            
            log_level=logging.getLevelName(log_level_string)
        except:
            log_level=default_log_level
        return log_level


    #LogをListに貯める機能のあるLog
    def log(self , message , level = "INFO" , details={} , flag_print = True , setting_dictionary = None , message_lists = None):
        if setting_dictionary is None:
            setting_dictionary = self.Setting
        if message_lists is None:
            message_lists = self.Log_Lists

        #辞書形式のlog dataを貯める
        log_message = {
            "date": datetime.datetime.now(),
            "level": level,
            "message": message
        }
        if details != {}:
            log_message.update(details)
        #dateをdetailsの中のdateで上書きしてフォーマットを合わせる事ができる仕様。
        date = log_message["date"]
        if type(date) == datetime.datetime:
            log_message["date"]=date.strftime( setting_dictionary.get("time_format",self.TIME_FORMAT))
        if setting_dictionary.get("log_function", False):
            frame = inspect.currentframe().f_back
            function_information = {"function":frame.f_code.co_name}
            if setting_dictionary.get("log_arguments", False):
                arguments = {}
                for key , value in frame.f_locals.items():
                    if key == "self":
                        continue
                    try:
                        arguments[key] = str(value)
                    except:
                        arguments[key] = "<skip>"
                function_information["arguments"] = arguments
            log_message.update(function_information)

        if flag_print:
            #setting_log_level = setting_dictionary.get("log_level",self.default_log_console_level)
            log_level = self.Log_Level_Get(level) 

            message = json.dumps(log_message , ensure_ascii=False)
            self.logger_console.log(log_level , message)
            #print(self.logger_console.handlers)
            
        message_lists.append(log_message)
        return message_lists


    def MessageList_Write(self , file_path_list = None , message_lists = None,log_level_string="INFO"):
        if file_path_list is None:
            file_path_list = self.FilePathList
        if message_lists is None:
            message_lists = self.Log_Lists
        if type(file_path_list) is list:
            temporary_list = file_path_list
        else:
            temporary_list = [file_path_list]
        message_list=[]
        for file_path in temporary_list:
            FileControl.Manage_File(file_path,message_list=message_list)
            # 辞書形式DataをJson形式のファイルに追記
            with open(file_path , 'a') as file:
                for message in message_lists:
                    message_level = self.Log_Level_Get(message.get("level"),logging.WARNING)
                    log_level = self.Log_Level_Get(log_level_string)
                    if log_level <= message_level:
                        file.write(json.dumps(message , ensure_ascii=False)+"\n")
        #self.log("","INFO",details = message_list)
                
    def MessageList_Clear(self , message_lists = Log_Lists):
        message_lists.clear()

def Log_MessageFormat(message):
    log_message='[' + str(datetime.datetime.now())+']' + message +'\n'
    return log_message

#LogをListに貯める動作。
def Log_MessageAdd(message_list , message , flag_print = False):
    if flag_print == True:
        print(message)
    message_list.append(Log_MessageFormat(message))

#MessageをFileに書き込む
def Write_Message(file_path , message):
    file = open(file_path , 'a')
    file.write(message)
    file.close()
    
def Clear_MessageList(message_list):
    message_list.clear()

#Message ListをFileに書き込む
def Write_MessageList(file_path , message_list):
    FileControl.Manage_File(file_path , message_list = message_list)
    
    file = open(file_path , 'a')
    file.writelines(message_list)
    file.close()


def get_error_dictionary():
    exc_type , exc_value , exc_traceback = sys.exc_info()
    error_information_dictionary ={
        "error": {
            'type': exc_type.__name__ , 
            'message': str(exc_value) , 
            'function': exc_traceback.tb_frame.f_code.co_name , 
            'lineno': exc_traceback.tb_lineno , 
            'filename': exc_traceback.tb_frame.f_code.co_filename
        }
    }
    return error_information_dictionary

