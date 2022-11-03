#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import tkinter



root = tkinter.Tk()
root.title(u"Software Title")
root.geometry("400x300")


#
# グローバル変数
#
hLabel = []             #ラベルのハンドルを格納します
hCheck = []             #チェックボックスのハンドルを格納します
CheckVal = []           #チェックボックスにチェックが入っているかどうかを格納します
hEdit = []   


#
# チェックボックスのチェック状況を取得する
#
def check(event):
    for n in range(len(CheckVal)):
        if CheckVal[n].get() == True:
            label = tkinter.Label(text=u"チェックされています")
            label.place(x=100, y=20*n + 50)
        else:
            label = tkinter.Label(text=u"チェックされていません")
            label.place(x=100, y=20*n + 50)

        #ラベルのハンドルを追加
        hLabel.append(label)


#
# チェックボックスを動的に作成
#
def make(event):
    #作成するチェックボックスの個数（Entryの値）を取得
    num = Entry1.get()

    #既出のチェックボックスやラベルを削除
    for n in range(len(hCheck)):
        hCheck[n].destroy()
        hLabel[n].destroy()
        hEdit[n].destroy()

    #配列を空にする
    del CheckVal[:]
    del hCheck[:]
    del hLabel[:]
    del hEdit[:]

    #Entry1に入力された値分ループ
    for n in range(int(num)):
        #BooleanVarの作成
        bl = tkinter.BooleanVar()

        #チェックボックスの値を決定
        bl.set(False)

        #チェックボックスの作成
        b = tkinter.Checkbutton(text = "項目" + str(n+1), variable = bl)
        b.place(x=5, y=20*n + 50)

        edit_box=tkinter.Entry(root)
        edit_box.place(x=100,y=20*n+50)
        #edit_box.pack(side= tkinter.TOP, expand=True,fill= tkinter.BOTH)        


        #チェックボックスの値を，リストに追加
        CheckVal.append(bl)

        #チェックボックスのハンドルをリストに追加
        hCheck.append(b)

        hEdit.append(edit_box)

#
# エディットボックスを動的に作成
#
def Dictionary_MakeInput(dictionary_input):
    #作成するチェックボックスの個数（Entryの値）を取得
    dictionary_number = len(dictionary_input)

    #既出のチェックボックスやラベルを削除
    for n in range(len(hCheck)):
        hCheck[n].destroy()
        hLabel[n].destroy()
        hEdit[n].destroy()

    #配列を空にする
    del CheckVal[:]
    del hCheck[:]
    del hLabel[:]
    del hEdit[:]

    #Entry1に入力された値分ループ
    for n in range(dictionary_number):
        key=list( dictionary_input)[n]
        value=dictionary_input[key]
        #BooleanVarの作成
        bl = tkinter.BooleanVar()

        #チェックボックスの値を決定
        bl.set(False)

        #チェックボックスの作成
        b = tkinter.Checkbutton(text = key, variable = bl)
        b.place(x=5, y=20*n + 50)

        edit_box=tkinter.Entry(root)
        edit_box.insert(tkinter.END,value)
        edit_box.place(x=100,y=20*n+50)
        #edit_box.pack(side= tkinter.TOP, expand=True,fill= tkinter.BOTH)        


        #チェックボックスの値を，リストに追加
        CheckVal.append(bl)

        #チェックボックスのハンドルをリストに追加
        hCheck.append(b)

        hEdit.append(edit_box)

def Event_DictionaryInput(event):
    dictionary_input={"A":"1","B":"2","C":"3"}
    Dictionary_MakeInput(dictionary_input)


Dictionary_MakeInput


button1 = tkinter.Button(root, text=u'Checkbuttonの作成',width=20)
#button1.bind("<Button-1>",make)
button1.bind("<Button-1>",Event_DictionaryInput)
button1.place(x=90, y=5)

button2 = tkinter.Button(root, text=u'チェックの取得',width=15)
button2.bind("<Button-1>",check)
button2.place(x=265, y=5)

Entry1 = tkinter.Entry(root, width=10)
Entry1.place(x=5, y=5)

root.after(10000, lambda: root.destroy())
root.mainloop()
