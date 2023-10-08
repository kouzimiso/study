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

def Archive_SizeOverFile(file_path,file_maxsize, settings_dictionary={},message_list=[]):
    if os.path.exists(file_path):
        filesize = os.path.getsize(file_path)
        if file_maxsize < filesize:
            root_ext_pair = os.path.splitext(file_path)
            new_path=Rename.Name_AddDays(file_path)
            try:
                os.rename(file_path, new_path) 
            #except PermissionError:
            except :
                message_list.append({
                    "message" :"File is lock. ",
                    "file_path" : file_path
                    })
                
        
def GetFileList(folder_path):
    try:
        files = os.listdir(folder_path)
        return files
    except FileNotFoundError:
        print(f"フォルダ '{folder_path}' が存在しません。")

# folder_path: 空き容量確保のために削除できるファイルがあるフォルダのパス
# folder_maxsize: 削除判断となるフォルダの容量
# files_maxnumber: 削除判断となるFileの数
def Delete_OldFiles(folder_path,  folder_maxsize , files_maxnumber , settings_dictionary={},message_list=[]):
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
def ManageFile(file_path , file_maxsize = 65536, archivefolder_path ="" , folder_maxsize = 1048576, files_maxnumber =100,message_list=[]):
    Archive_SizeOverFile(file_path ,file_maxsize)
    if os.path.exists(archivefolder_path):
        folder_path = archivefolder_path
    else:
        folder_path = pathlib.Path(file_path).parent
    Delete_OldFiles(folder_path ,  folder_maxsize , files_maxnumber,message_list)
    return True

# Defaultの辞書Dataを設定
default_dictionary ={
    "action":"ManageFile",
    "file_path":"./test/test.png" ,
    "file_maxsize": 100,
    "archivefolder_path": "./test",
    "folder_maxsize" : 1048576,
    "files_maxnumber" : 5
}
def Execute(settings_dictionary):
    action = settings_dictionary.get("action","ManageFile")
    file_path = settings_dictionary.get("file_path")
    file_maxsize = settings_dictionary.get("file_maxsize")
    archivefolder_path = settings_dictionary.get("archivefolder_path")
    folder_maxsize = settings_dictionary.get("folder_maxsize")
    files_maxnumber = settings_dictionary.get("files_maxnumber")

    result_dictionary ={}
    message_list = []
    if action == "ManageFile":
        result = ManageFile(file_path , file_maxsize, archivefolder_path , folder_maxsize , files_maxnumber,message_list)
        result_dictionary["result"]= result
    elif action == "GetFileList":
        result_dictionary["file_path_list"] = GetFileList(file_path)

    if(message_list != []):
        result_dictionary["message"] = message_list
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    settings_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    result_dictionary = Execute(settings_dictionary)
    FunctionUtility.Result(result_dictionary)

if __name__ == "__main__":
    main()

