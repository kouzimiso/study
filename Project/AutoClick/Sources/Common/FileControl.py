#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import pathlib

import Rename

import datetime
import FunctionUtility

def Get_FolderSize(folder_path):
    total = 0
    with os.scandir(folder_path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += Get_FolderSize(entry.path)
    return total

def Get_FilesNumber(folder_path):
    total = 0
    with os.scandir(folder_path) as it:
        for entry in it:
            if entry.is_file():
                total += 1
            elif entry.is_dir():
                total += Get_FolderSize(entry.path)
    return total

def Archive_SizeOverFile(file_path,file_maxsize, setting_dictionary={},message_list=[]):
    if os.path.exists(file_path):
        filesize = os.path.getsize(file_path)
        if file_maxsize < filesize:
            root_ext_pair = os.path.splitext(file_path)
            newpath=Rename.Name_AddDays(file_path)
            try:
                os.rename(file_path, newpath) 
            #except PermissionError:
            except :
                message_list.append({
                    "message" :"File is lock. ",
                    "file_path" : file_path
                    })
                
        

# folder_path: 空き容量確保のために削除できるファイルがあるフォルダのパス
# folder_maxsize: 削除判断となるフォルダの容量
# files_maxnumber: 削除判断となるFileの数
def Delete_OldFiles(folder_path,  folder_maxsize , files_maxnumber , setting_dictionary={},message_list=[]):
    files = []
    folders = []
    # サブフォルダのPathオブジェクトをイテレート。ファイルとフォルダに振り分ける。
    for p in pathlib.Path(folder_path).rglob("*"): 
        if p.is_file():
            files.append(p)
        else:
            folders.append(p)
    # 更新日時の昇順にファイルの相対パスをソート。
    files.sort(key=lambda x: x.stat().st_mtime)  
    for file in files:  # 古いファイルからイテレート。
        folder_size=Get_FolderSize(folder_path)
        files_number=Get_FilesNumber(folder_path)
        message_details={
            "date" : datetime.datetime.now(),
            "folder size":str(folder_size)+"/"+str(folder_maxsize),
            "file number": str(files_number)+"/"+str(files_maxnumber)
        }
        # 規定の空き容量、File数を超えた場合
        if folder_maxsize <folder_size :
            try:
                os.remove(file)  # ファイルを削除。
                message = "Size Over the oldest file " + file.name + " has been removed."
            except PermissionError:
                message = "File is lock."
                message_details["file_path"]=file.name
                message_details["message"]=message
                message_list.append(message_details)
                continue

        elif files_maxnumber < files_number :
            try:
                os.remove(file)  # ファイルを削除。
                message = "File Number Over.The oldest file " + file.name + " has been removed."
            except PermissionError:
                message = "File(" + file.name + ") is lock."
                message_details["message"]=message
                message_list.append(message_details)
                continue

        else:  # 空き容量が確保出来ていた時はループを出る。
            break
        message_details["message"]=message
        message_list.append(message_details)

    folders.sort(key=lambda x: len(x.parents), reverse=True )  # 階層が深い降順に並べる。
    for folder in folders:  # 深い階層から空フォルダを削除する。
        if next(folder.iterdir(), None) is None:  # フォルダ内に子要素がない時。
            folder.rmdir()  # フォルダを削除。 
            message_list.append({
                    "message" :"The empty folder has been removed. ",
                    "folder_path" : folder
            })
def Manage_File(file_path , file_maxsize = 65536, archivefolder_path ="" , folder_maxsize = 1048576, files_maxnumber =100,message_list=[]):
    Archive_SizeOverFile(file_path ,file_maxsize)
    if os.path.exists(archivefolder_path):
        folder_path = archivefolder_path
    else:
        folder_path = pathlib.Path(file_path).parent
    Delete_OldFiles(folder_path ,  folder_maxsize , files_maxnumber,message_list)
    return True

def main(argument_dictionary):
    file_path = argument_dictionary.get("file_path")
    file_maxsize = argument_dictionary.get("file_maxsize")
    archivefolder_path = argument_dictionary.get("archivefolder_path")
    folder_maxsize = argument_dictionary.get("folder_maxsize")
    files_maxnumber = argument_dictionary.get("files_maxnumber")
    message_list = []
    result = Manage_File(file_path , file_maxsize, archivefolder_path , folder_maxsize , files_maxnumber,message_list)

    result_dictionary={"result" : result}
    if(message_list != []):
        result_dictionary["message"] = message_list
    FunctionUtility.Result(result_dictionary)

if __name__ == "__main__":
    # Defaultの辞書Data
    default_dictionary ={
        "file_path":"./test/test.png" ,
        "file_maxsize": 100,
        "archivefolder_path": "./test",
        "folder_maxsize" : 1048576,
        "files_maxnumber" : 5
    }
    argument_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    main(argument_dictionary)
