import sys
from PIL import ImageGrab
from enum import Enum
import PIL
import cv2
import pyautogui
import hashlib
import glob
import numpy as np
import threading
import os

import Rename
import FunctionUtility

class VIRTICAL_ALIGN(Enum):
    UNKNOWN=0
    TOP= 1
    MIDDLE= 2
    BOTTOM = 3

class HOLIZONTAL_ALIGN(Enum):
    UNKNOWN=0
    LEFT= 1
    CENTER= 2
    RIGHT = 3


def open(image_file_path):
    return PIL.Image.open(image_file_path)
    

def CVImageCrop_ByList(image_source,list_image_file_path,list_image_position):
    loop=0
    for file_path in list_image_file_path:
        #imageのtrimming(img[top : bottom, left : right])
        #ScreenShootのData部分を画像に保存する
        if list_image_position[loop] is not None:
            image_position = list_image_position[loop]
            top=image_position[1]
            bottom=image_position[3]
            left=image_position[0]
            right=image_position[2]
            #print("top:"+ str(top) +" bottom:"+ str(bottom) +" left:" + str(left) + " right:" + str(right) )
            image_crop=image_source[top:bottom,left:right]
            cv2.imwrite(file_path, image_crop)
        loop = loop + 1

def CropAndAlign_ByFilePath(image_file_path,
                x,
                y,
                width,
                height,
                image_holizontal_align = HOLIZONTAL_ALIGN.LEFT,
                image_virtical_align =VIRTICAL_ALIGN.TOP,
                holizontal_align = 0,
                virtical_align = 0
                ):        
    image=PIL.Image.open(image_file_path)
    return CropAndAlign(image,
                x,
                y,
                width,
                height,
                image_holizontal_align,
                image_virtical_align,
                holizontal_align,
                virtical_align
                )

def CropAndAlign(image,
                x,
                y,
                width,
                height,
                image_holizontal_align = HOLIZONTAL_ALIGN.LEFT,
                image_virtical_align = VIRTICAL_ALIGN.TOP,
                holizontal_align = 0,
                virtical_align = 0,
                ):
    if holizontal_align == 0:
        if image_holizontal_align == HOLIZONTAL_ALIGN.CENTER:
            holizontal_align= HOLIZONTAL_ALIGN.CENTER
        elif image_holizontal_align == HOLIZONTAL_ALIGN.LEFT:
            holizontal_align= HOLIZONTAL_ALIGN.LEFT
        else:
            holizontal_align= HOLIZONTAL_ALIGN.LEFT
            
    if virtical_align == 0 :
        if image_virtical_align == VIRTICAL_ALIGN.MIDDLE:
            virtical_align=VIRTICAL_ALIGN.MIDDLE
        elif image_virtical_align == VIRTICAL_ALIGN.TOP:
            virtical_align=VIRTICAL_ALIGN.TOP
        else:
            virtical_align=VIRTICAL_ALIGN.BOTTOM

    image_width, image_height = image.size


    #横整列の位置変換
    if holizontal_align == HOLIZONTAL_ALIGN.CENTER:
        left = x - width / 2
        right = x + width / 2
    elif holizontal_align == HOLIZONTAL_ALIGN.RIGHT:
        left = x - width
        right = x
    else:
        left = x
        right = x + width        

    #縦整列の位置変換
    if virtical_align == VIRTICAL_ALIGN.MIDDLE:
        upper = y - height / 2
        lower = y + height / 2
    elif virtical_align == VIRTICAL_ALIGN.BOTTOM:
        upper = y - height
        lower = y
    else:
        upper = y
        lower = y + height        

    #画像横整列の位置変換
    if image_holizontal_align == HOLIZONTAL_ALIGN.CENTER:
        left = left + image_width / 2
        right = right + image_width / 2
    elif image_holizontal_align == HOLIZONTAL_ALIGN.RIGHT:
        left = left + image_width
        right = right + image_width

    #画像縦整列の位置変換
    if image_virtical_align == VIRTICAL_ALIGN.MIDDLE:
        upper = upper + image_height / 2
        lower = lower + image_height / 2
    elif image_virtical_align == VIRTICAL_ALIGN.BOTTOM:
        upper = upper + image_height
        lower = lower + image_height

    #左位置マイナスの場合は0に書き換え
    if left < 0:
        right = right - left
        left = 0

    #上位置マイナスの場合は0に書き換え
    if upper < 0:
        lower = lower -upper
        upper = 0

    print("left:%d upper:%d right:%d lower:%d" %(left,upper,right,lower))
    return image.crop((left,upper,right,lower) )

def Image_AroundMouse(file_path, flag_overwrite=True, wide=0, height=0, dupplicate_format="{}({:0=3}){}"):
    x, y = pyautogui.position()
    Image_AroundPoint(file_path, flag_overwrite, x, y,
                      wide, height, dupplicate_format)

def Image_AroundPoint(file_path, flag_overwrite=True, x=0, y=0, wide=0, height=0, dupplicate_format="{}({:0=3}){}"):
    x = max(0, x - wide/2)
    y = max(0, y - height/2)
    CaptureImage(file_path, flag_overwrite, x, y, wide, height, dupplicate_format)

def point2ToXYWH(x1, y1, x2=0, y2=0):
  
    if x2 <= x1:
        x = x2
        w = x1-x2
    else:
        x = x1
        w = x2-x1
    if y2 <= y1:
        y = y2
        h = y1-y2
    else:
        y = y1
        h = y2-y1
    return x,y,w,h

def CaptureImage(file_path, flag_overwrite=True, x=0, y=0, wide=0, height=0, dupplicate_format="{}({:0=3}){}"):
    if flag_overwrite == False:
        path = Rename.duplicate_rename(file_path, dupplicate_format)
    else:
        path = file_path
    if wide == 0 or height == 0:
        ImageGrab.grab().save(path)
    else:
        bbox_w = wide
        bbox_h = height
        bbox_x = x
        bbox_y = y
        ImageGrab.grab(bbox=(bbox_x,  bbox_y, bbox_x + bbox_w, bbox_y + bbox_h)).save(path)

def GenerateRandomImageBySetting(setting_dictionary):
    width = setting_dictionary.get("width",400)
    height = setting_dictionary.get("height",200)
    file_path = setting_dictionary.get("file_path","")
    flag_show_image = setting_dictionary.get("show_image","")

    image = GenerateRandomImage(width, height)
    try:
        if(file_path != ""):
            result = cv2.imwrite(file_path,image)
        else:
            result = False
        if flag_show_image:
            def show_image(file_path,image):
                cv2.imshow(file_path,image)
            display_thread = threading.Thread(target=show_image, args=(file_path,image))
            display_thread.start()

        return {"result": result}
    except Exception as e:
        return {"result": False, "error_message": str(e)}
    
def GenerateRandomImage(width, height):
    # 0から255のランダムなピクセル値で画像を生成
    random_image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return random_image

def GenerateTextImageBySetting(setting_dictionary):
    text = setting_dictionary.get("text","")
    font_size = setting_dictionary.get("font_size",24)
    width = setting_dictionary.get("width",400)
    height = setting_dictionary.get("height",200)
    file_path = setting_dictionary.get("file_path","")
    flag_show_image = setting_dictionary.get("show_image",False)

    image = GenerateTextImage(text, font_size, width, height)
    try:
        if(file_path != ""):
            result = image.save(file_path)
            if result == None:
                result = True
        else:
            result = False
        if flag_show_image:
            def show_image():
                image.show()
            display_thread = threading.Thread(target=show_image)
            display_thread.start()
            #display_thread.join()
            
        return {"result": result}
    except Exception as e:
        return {"result": False, "error_message": str(e)}

def GenerateTextImage(text, font_size=24, width=400, height=200):
    # 白い背景の画像を生成
    image = PIL.Image.new('RGB', (width, height), 'white')
    draw = PIL.ImageDraw.Draw(image)

    # フォントとテキストを指定
    font = PIL.ImageFont.truetype('arial.ttf', font_size)
    
    # テキストを中央に配置
    text_width, text_height = draw.textsize(text, font)
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # テキストを画像に描画
    draw.text((x, y), text, fill='black', font=font)    
    return image

def DeleteDuplicateImageBySetting(setting_dictionary):
    directory_path = setting_dictionary.get("directory_path","")
    DeleteDuplicateImage(directory_path)
    return {"result":True}


def DeleteDuplicateImage(directory_path):
    flist = []
    fmd5 = []
    dl = []
    for e in ['png', 'jpg']: flist.extend(glob('%s/*.%s'%(directory_path,e)))
    for fn in flist:
        with open(fn, 'rb') as fin:
            data = fin.read()
            m = hashlib.md5(data)
            fmd5.append(m.hexdigest())
    for i in range(len(flist)):
        if flist[i] in dl: continue
        for j in range(i+1, len(flist)):
            if flist[j] in dl: continue
            if fmd5[i] == fmd5[j] and not flist[j] in dl:
                dl.append(flist[j])
    for a in dl: os.remove(a)

def Execute(setting_dictionary):
    action = setting_dictionary.get("action")
    result_dictionary={"result":False}
    if action == 'GENERATE_TEXT_IMAGE':
        result_dictionary = GenerateTextImageBySetting(setting_dictionary)
    elif action == 'GENERATE_RANDOM_IMAGE':
        result_dictionary = GenerateRandomImageBySetting(setting_dictionary)
    elif action == 'DELETE_DUPLICATE_IMAGE':
        DeleteDuplicateImageBySetting(setting_dictionary)
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Defaultの辞書Dataを設定。
    default_dictionary ={
        # 処理
        "action" : "GENERATE_TEXT_IMAGE",#"GENERATE_TEXT_IMAGE","GENERATE_RANDOM_IMAGE","DeleteDuplicateImage"
    }
    generate_text_image_dictionary ={
        "width" : 400,
        "height" : 200,
        "file_path" : "../Test/test_image.png",
        "show_image" : True,
        "text": "test",
        "font_size": 24
    }
    generate_random_image_dictionary ={
        "width" : 400,
        "height" : 200,
        "file_path" : "../Test/test_image.png",
        "show_image" : True
    }
    delete_duplicate_image_dictionary ={
        "folder_path" : "../Test/"
    }
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    setting_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    if  setting_dictionary.get("action","") =="GENERATE_TEXT_IMAGE":
        setting_dictionary = FunctionUtility.ArgumentGet(generate_text_image_dictionary,setting_dictionary)
    elif  setting_dictionary.get("action","") =="GENERATE_RANDOM_IMAGE":
        setting_dictionary = FunctionUtility.ArgumentGet(generate_random_image_dictionary,setting_dictionary)
    elif  setting_dictionary.get("action","") =="DELETE_DUPLICATE_IMAGE":
        setting_dictionary = FunctionUtility.ArgumentGet(delete_duplicate_image_dictionary,setting_dictionary)
    result_dictionary = Execute(setting_dictionary)
    FunctionUtility.Result(result_dictionary)

if __name__ == "__main__":
    main()

