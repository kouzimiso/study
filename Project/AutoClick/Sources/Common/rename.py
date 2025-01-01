import os
import shutil
import datetime

def duplicate_rename(file_path,dupplicate_format="{}({:0=3}){}"):
    if os.path.exists(file_path):
        name, ext = os.path.splitext(file_path)
        i = 1
        while True:
            # 数値を3桁とする
            new_name = dupplicate_format.format(name, i, ext)
            if not os.path.exists(new_name):
                return new_name
            i += 1
    else:
        return file_path

def Name_AddDays(file_path):
    date_now = datetime.datetime.now()
    file_path, file_ext = os.path.splitext(file_path)
    #os.rename(file_path, date_now.strftime("%Y%m%d %H%M%S") + file_ext)
    
    return file_path +"_"+ date_now.strftime("%Y%m%d_%H%M%S") + file_ext


