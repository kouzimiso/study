import sys
from PIL import ImageGrab
from enum import Enum
import PIL
import cv2
import pyautogui


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
    Image_Capture(file_path, flag_overwrite, x, y, wide, height, dupplicate_format)
    
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

def Image_Capture(file_path, flag_overwrite=True, x=0, y=0, wide=0, height=0, dupplicate_format="{}({:0=3}){}"):
    if flag_overwrite == False:
        path = rename.duplicate_rename(file_path, dupplicate_format)
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

