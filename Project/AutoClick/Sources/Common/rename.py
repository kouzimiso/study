import os
import shutil

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

