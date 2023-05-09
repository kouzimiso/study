# coding:utf-8
import sys
import pyperclip
import pynput
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.uix.widget import Widget
from kivy.core.text import LabelBase,DEFAULT_FONT
from kivy.resources import resource_add_path
#from kivy.lang import Builder

from kivy.config import Config
from kivy.properties import StringProperty
from kivy.clock import Clock

sys.path.append("../Common")
sys.path.append("../Models")
sys.path.append("../ViewModels")
sys.path.append("../Views")
import ImageControl
import ocr
Config.set('modules', 'inspector', '')


resource_add_path('../../Fonts')
#kivy.core.text.LabelBase.register(kivy.core.text.DEFAULT_FONT,'mplus-2c-regular.ttf')
LabelBase.register(DEFAULT_FONT,'mplus-2c-regular.ttf')

Config.set('graphics','width',640)
Config.set('graphics','height',480)
Config.set('graphics','resizable',1)


FilePath="../../Images/image_capture/Image_screen.png"
CaptureX=0
CaptureY=0
CaptureWidth=100
CaptureHeight=100
OCR_Text="<OCR Reader>"
Sequence_ImageCapture = 0


class OCRWidget(Widget):
    ocr_text = StringProperty(OCR_Text)
    file_path= StringProperty(FilePath)
    capture_width= StringProperty(str(CaptureWidth))
    capture_height= StringProperty(str(CaptureHeight))
    #self.ids["text_input_filepath"].text=FilePath
    event = None

    def __init__(self, **kwargs):
        #Clock.schedule_once(my_callback, 1)
        super(OCRWidget, self).__init__(**kwargs)
        #Clock.schedule_interval(self.my_callback, 1)
        
    def capture_clicked(self):
        global Sequence_ImageCapture        
        Sequence_ImageCapture = 1
        print("Sequence_ImageCapture1")
        self.event=Clock.schedule_interval(self.my_callback, 1)

        return
    
    def ocr_clicked(self):
        self.image_update()
        # 画面Captureの文字認識
        ocr_instance = OCR.OCR()
        ocr_instance.Setting_BuilderText(6)
        OCR_Text = ocr_instance.Recognition_ByFilePath(self.file_path, "jpn")
        self.ocr_text = OCR_Text
        print(OCR_Text)
        pyperclip.copy(OCR_Text)
    
    def image_update(self):
        global FilePath
        global CaptureWidth
        global CaptureHeight
        print("update")
        self.capture_width= str(CaptureWidth)
        self.capture_height= str(CaptureHeight)
        self.file_path=""
        self.file_path=FilePath
        return
        
    #def on_touch_down(self,touch):
    #    if Widget.on_touch_down(self, touch):
    #        return
    #def on_touch_up(self,touch):
    #    if Widget.on_touch_up(self, touch):
    #        return
    def on_text_validate_filepath(self,value):
        global FilePath
        self.file_path = value
        FilePath = value
        print("text input %s", value)

        
    def on_text_validate_capture_width(self,value):
        global CaptureWidth
        self.capture_width=value
        CaptureWidth=int(value)
        print("text input %s",value)
        
    def on_text_validate_capture_height(self,value):
        global CaptureHeight
        self.capture_height= value
        CaptureHeight=int(value)
        print("text input %s", value)        

    def my_callback(self,dt):
        global CaptureX
        global CaptureY
        global CaptureWidth
        global CaptureHeight
        global Sequence_ImageCapture
        global FilePath
        if 3 <= Sequence_ImageCapture  :
            print ('My callback is called')
            #capture_width= str(CaptureWidth)
            #capture_height= str(CaptureHeight)
            #file_path=""
            #file_path=FilePath
            Sequence_ImageCapture=Sequence_ImageCapture+1
            print("Sequence_ImageCapture %d",Sequence_ImageCapture)
            self.image_update()

        if 5 <= Sequence_ImageCapture:
            Sequence_ImageCapture=0
            self.event.cancel
        return
        
class Gui_ocrApp(App):
    def __init__(self, **kwargs):
        super(Gui_ocrApp,self).__init__(**kwargs)
        self.title="greeting"

    def build(self):
        return OCRWidget()


def move(x, y):
    print('マウスポインターは {0} へ移動しました'.format((x, y)))


def capture_start(x, y):
        global CaptureX
        global CaptureY
        CaptureX=x
        CaptureY=y
        print("touch down x:"+str(CaptureX)+"y:"+str(CaptureY))
        return

def capture_end(x, y):
        global CaptureX
        global CaptureY
        global CaptureWidth
        global CaptureHeight
        #2pointを1pointと大きさに変換
        CaptureX, CaptureY,CaptureWidth,CaptureHeight = ImageControl.point2ToXYWH(x,y,CaptureX,CaptureY)
        ImageControl.Image_Capture(FilePath ,True ,CaptureX,CaptureY,CaptureWidth ,CaptureHeight)
        print( "touch up x:"+str(CaptureX)+"y:"+str(CaptureY)+"w:"+str(CaptureWidth)+"h:"+str(CaptureHeight))
        return
        
def click(x, y, button, pressed):
    global Sequence_ImageCapture
    #Auto.Image_AroundMouse(file_path = FilePath ,wide=CaptureWidth , height=CaptureHeight)

    if pressed:     # クリックしたら
        #print("touch_down")
        if Sequence_ImageCapture == 1:
            capture_start(x, y)
            Sequence_ImageCapture=2
            print("Sequence_ImageCapture2")

    elif not pressed:     # クリックを離したら
        #print("touch_up")
        if Sequence_ImageCapture == 2:
            capture_end(x, y)
            Sequence_ImageCapture=3
            print("Sequence_ImageCapture3")
            #mouse_listener_stop()
            #return False    # Listenerを止める
    return

if __name__=="__main__":
    mouse_listener = pynput.mouse.Listener(on_click=click) #,on_scroll=scroll)
    mouse_listener.start()
    
    Gui_ocrApp().run()
