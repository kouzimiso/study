#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import pathlib

import rename
import log

MessageList=[]

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

def Archive_SizeOverFile(file_path,file_maxsize, setting={}):
    global MessageList 
    if os.path.exists(file_path):
        filesize = os.path.getsize(file_path)
        if file_maxsize < filesize:
            root_ext_pair = os.path.splitext(file_path)
            newpath=rename.Name_AddDays(file_path)
            try:
                os.rename(file_path, newpath) 
            except PermissionError:
                print("File " + file_path + " is lock.")
                #logger = log.Logs(setting)
                #MessageList = logger.error("File " + file_path + " is lock." )
        

# folder_path: 空き容量確保のために削除できるファイルがあるフォルダのパス
# folder_maxsize: 削除判断となるフォルダの容量
# files_maxnumber: 削除判断となるFileの数
def Delete_OldFiles(folder_path,  folder_maxsize , files_maxnumber , setting={}):
    global MessageList 
    #logger = log.Logs(setting)
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
        message = {"folder size":str(folder_size)+"/"+str(folder_maxsize),"file number": str(files_number)+"/"+str(files_maxnumber)}
        print(message)
        #MessageList = logger.log(message , "INFO")
        # 規定の空き容量、File数を超えた場合
        if folder_maxsize <folder_size :
            try:
                os.remove(file)  # ファイルを削除。
                message = "Size Over the oldest file " + file.name + " has been removed."
                #MessageList = logger.log(message,"INFO")
            except PermissionError:
                message = "File( " + file.name + ") is lock."
                #MessageList = logger.error(message)
                continue

        elif files_maxnumber < files_number :
            try:
                os.remove(file)  # ファイルを削除。
                message = "File Number Over.The oldest file " + file.name + " has been removed."
                #MessageList = logger.log(message,"INFO")
            except PermissionError:
                message = "File(" + file.name + ") is lock."
                #MessageList = logger.error(message)
                continue

        else:  # 空き容量が確保出来ていた時はループを出る。
            break
        print(message)
    folders.sort(key=lambda x: len(x.parents), reverse=True)  # 階層が深い降順に並べる。
    for folder in folders:  # 深い階層から空フォルダを削除する。
        if next(folder.iterdir(), None) is None:  # フォルダ内に子要素がない時。
            folder.rmdir()  # フォルダを削除。 
            #MessageList = logger.log("The empty folder " + folder.name + "has been removed.")
            print("The empty folder " + folder.name + "has been removed.")

def Manage_File(file_path , file_maxsize = 65536, archivefolder_path ="" , folder_maxsize = 262144, files_maxnumber =100):
    Archive_SizeOverFile(file_path ,  file_maxsize)

    if os.path.exists(archivefolder_path):
        folder_path = archivefolder_path
    else:
        folder_path = pathlib.Path(file_path).parent
    Delete_OldFiles(folder_path ,  folder_maxsize , files_maxnumber)

def main(file_path , file_maxsize, archivefolder_path , folder_maxsize , files_maxnumber):
    Manage_File(file_path , file_maxsize, archivefolder_path , folder_maxsize , files_maxnumber)

if __name__ == "__main__": 
    defaults = "C:/Users/kouzi/Dropbox/Works_Shibaura/Nowworks/Auto/AutoClick/Sources/Test/testdir/test_kivy3.py" , 100 ,"", 100000 , 5  # デフォルト引数。
    args = list(sys.argv)  # コマンドラインの引数を取得。インデックス0はスクリプトのパスなど。
    for i in defaults[len(args)-1:]:  # 足りない引数をデフォルトから補う。
        args.append(i)
    args[2] = int(args[2])  # 引数は文字列で返るので整数に変換する。
    main(*args[1:])
