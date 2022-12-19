#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
def main(folderpath, freespacerate, disk):  # disk: 容量割合計算の分母にするフォルダのパス, folderpath: 空き容量確保のために削除できるファイルがあるフォルダのパス、freespacerate: 空き容量の%を整数で渡す。
    files = []
    folders = []
    for p in Path(folderpath).rglob("*"):  # サブフォルダのPathオブジェクトをイテレート。ファイルとフォルダに振り分ける。
        if p.is_file():
            files.append(p)
        else:
            folders.append(p)
    files.sort(key=lambda x: x.stat().st_mtime)  # 更新日時の昇順にファイルの相対パスをソート。
    for file in files:  # 古いファイルからイテレート。
        statvfs = os.statvfs(disk)  # ルートディレクトリの情報を取得。動くのはUnixのみ。
        if int(statvfs.f_bavail/statvfs.f_blocks*100)<freespacerate:  # 規定の空き容量割合を達成していない時。
            file.unlink()  # ファイルを削除。
            print("The oldest file {} has been removed.".format(file.name))
        else:  # 空き容量が確保出来ていた時はループを出る。
            break 
    folders.sort(key=lambda x: len(x.parents), reverse=True)  # 階層が深い降順に並べる。
    for folder in folders:  # 深い階層から空フォルダを削除する。
        if next(folder.iterdir(), None) is None:  # フォルダ内に子要素がない時。
            folder.rmdir()  # フォルダを削除。 
            print("The empty folder {} has been removed.".format(folder.name))
if __name__ == "__main__": 
    defaults = 'C:/Users/kouzi/Dropbox/Works_Shibaura/Nowworks/Auto/AutoClick/Sources/Test/test_file', 5, "/"  # デフォルト引数。
    args = list(sys.argv)  # コマンドラインの引数を取得。インデックス0はスクリプトのパスなど。
    for i in defaults[len(args)-1:]:  # 足りない引数をデフォルトから補う。
        args.append(i)
    args[2] = int(args[2])  # 引数は文字列で返るので整数に変換する。
    main(*args[1:])
