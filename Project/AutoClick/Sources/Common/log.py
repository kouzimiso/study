## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import datetime
import os
from enum import Enum

class END_ACTION(Enum):
    BREAK = 0
    FOLDER_END_BREAK = 1
    CONTINUE = 2

        
def Log_MessageFormat(message):
    log_message='[' + str(datetime.datetime.now())+']' + message +'\n'
    return log_message

#LogをListに貯める動作。
def Log_MessageAdd(message_list,message):
    print(message)
    message_list.append(Log_MessageFormat(message))

#MessageをFileに書き込む
def Write_Message(file_path,message):
    file = open(file_path,'a')
    file.write(message)
    file.close()
    
def Clear_MessageList(message_list):
    message_list.clear()

#Message ListをFileに書き込む
def Write_MessageList(file_path,message_list):
    file = open(file_path,'a')
    file.writelines(message_list)
    file.close()
