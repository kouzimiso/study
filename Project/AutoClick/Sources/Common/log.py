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
import LogMessage
import FunctionUtility
#class END_ACTION(Enum):
#    BREAK = 0
#    FOLDER_END_BREAK = 1
#    CONTINUE = 2

#JSONの設定Fileを読込み、Fileがない場合はDefault設定をPythonのLogging Classに設定する。
#LogはLog_append関数で現在の時間とメッセージとレベルを辞書形式でListに加えて貯める。
#Log_append関数で貯めたLogをlog_write関数でloggingのレベルでフィルタリングし、1回のFile書き込みで複数のLogをまとめてJSON.Line形式でFileに追記する
class Logs:
    def __init__(self , settings_dictionary = {}):
        self.Log_Lists = []
        self.Setting = {}
        self.default_log_console_level : str = "WARNING"
        #self.MESSAGE_FORMAT ="%(asctime)s %(levelname)s %(message)s"
        self.MESSAGE_FORMAT = "%(message)s"
        self.TIME_FORMAT = "%Y/%m/%d %H:%M:%S"
        self.FilePathList = ["../Log/log.json"]
        self.DEFAULT_FORMATTER = {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            #"json_default" : json.JSONEncoder.default , 
            #'()' : 'pythonjsonlogger.jsonlogger.JsonFormatter' , 
            "format" : self.MESSAGE_FORMAT , 
            "datefmt" : self.TIME_FORMAT 
        }
        self.CONSOLE_HANDLER = {
            "class" : "logging.StreamHandler" , 
            "formatter" : "json" , 
            "level" : "INFO"
        }
        self.FILE_HANDLERS = {
            "file" : { 
                "class" : "logging.FileHandler" , 
                "filename" : "../Log/log2.json" , 
                "formatter" : "json"
            },
            "console":self.CONSOLE_HANDLER
        }
        
        # デフォルトのログ設定
        self.DEFAULT_LOGGING_CONFIG = {
            "version" : 1 , 
            "disable_existing_loggers" : False , 
            "handlers" : self.FILE_HANDLERS , 
            "formatters" : {
                "json" : self.DEFAULT_FORMATTER
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
        self.Setup(settings_dictionary)
        
    def Setup(self , settings_dictionary = {}):
        if type(settings_dictionary) is not dict:
            settings_dictionary = {}
        self.Setting = settings_dictionary
        log_settings_path = settings_dictionary.get("log_settings_path")
        file_path_list = settings_dictionary.get("log_file_path_list",None)
        if file_path_list is not None:
            self.FilePathList = file_path_list
        # ログ設定ファイルの読み込み
        try:
            #path指定が無ければDefault設定、有れば設定をDictionary形式で読み込む
            if log_settings_path is None:
                config = self.DEFAULT_LOGGING_CONFIG
            else:
                with open(log_settings_path , 'rt') as f:
                    config = json.load(f)
        #except FileNotFoundError:
        except:
            with open("settings_log.json" , 'wt') as f:
                json.dump(self.DEFAULT_LOGGING_CONFIG , f , indent=4)
            config = self.DEFAULT_LOGGING_CONFIG
        logging.config.dictConfig(config)
        self.logger = logging.getLogger("file")

        self.logger_console = logging.getLogger("console")
        log_console_level = settings_dictionary.get("log_console_level",None)
        if log_console_level is not None:
            self.logger_console.setLevel(log_console_level)
        if not self.logger_console.handlers:
            handler = logging.StreamHandler(sys.stdout)
            self.logger_console.addHandler(handler)
        self.log_print_standard_output =  settings_dictionary.get("log_print_standard_output",False)

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
        error_information = LogMessage.Get_Error_Dictionary()
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
            if not isinstance(log_level, int):
                log_level=default_log_level
        except:
            log_level=default_log_level
        if not isinstance(log_level, int):
            log_level = logging.WARNING
        return log_level


    #LogをListに貯める機能のあるLog
    def log(self , message , level = "INFO" , details={} , flag_print = None , settings_dictionary = None , message_lists = None):
        if flag_print is None:
            flag_print = self.log_print_standard_output 
        if settings_dictionary is None:
            settings_dictionary = self.Setting
        if message_lists is None:
            message_lists = self.Log_Lists

        #辞書形式のlog data format
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
            log_message["date"]=date.strftime( settings_dictionary.get("time_format",self.TIME_FORMAT))
        if settings_dictionary.get("log_function", False):
            frame = inspect.currentframe().f_back
            function_information = {"function":frame.f_code.co_name}
            if settings_dictionary.get("log_arguments", False):
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
            #settings_log_level = settings_dictionary.get("log_level",self.default_log_console_level)
            log_level = self.Log_Level_Get(level) 
            message = json.dumps(log_message , ensure_ascii=False)
            #self.logger_console.log(log_level , message)
            message_level = self.Log_Level_Get(log_message.get("level"),logging.WARNING)
            if log_level <= message_level:
                print(log_message.get("date","")+" "+ log_message.get("message",""))
                
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
            FileControl.ManageFile(file_path,message_list=message_list)
            # 辞書形式DataをJson形式のファイルに追記
            with open(file_path , 'a') as file:
                for message in message_lists:
                    message_level = self.Log_Level_Get(message.get("level"),logging.WARNING)
                    log_level = self.Log_Level_Get(log_level_string)
                    if log_level <= message_level:
                        file.write(json.dumps(message , ensure_ascii=False)+"\n")
        #self.log("","INFO",details = message_list)
                
    def MessageList_Clear(self , message_lists = None):
        if message_lists is None:
            message_lists = self.Log_Lists
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
    FileControl.ManageFile(file_path , message_list = message_list)
    
    file = open(file_path , 'a')
    file.writelines(message_list)
    file.close()

def Execute(settings_dictionary):
    settings_dictionary["message"]= "test message"
    logger=Logs(settings_dictionary)
    logger.log("","",settings_dictionary)
    logger.MessageList_Write()
    #logger.MessageList_Clear()

    settings_dictionary["message"]= "test message2"
    settings_dictionary["log_file_path_list"]= ["../Log/log2.json","../Log/log3.json"]

    logger2=Logs(settings_dictionary)
    logger2.log("","",settings_dictionary)
    logger2.log("","",settings_dictionary)
    logger2.MessageList_Write()
    #logger2.MessageList_Clear()

    result_dictionary={"result" : True}
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Defaultの辞書Dataを設定。
    default_dictionary = {
        "log_settings_path": "./settings_log.json",
        "log_file_path_list": ["../Log/log.json"]

    }
    option_dictionary ={
        "message": "test message",
        "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "level": "INFO",
        "log_print_standard_output":True
    }
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    settings_dictionary = FunctionUtility.ArgumentGet(default_dictionary,option_dictionary)
    result_dictionary = Execute(settings_dictionary)
    FunctionUtility.Result(result_dictionary)



if __name__ == '__main__':
    main()


