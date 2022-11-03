import tkinter
import pynput
import sys
import PIL
import pyperclip
sys.path.append("../Common")
sys.path.append("../Models")
sys.path.append("../ViewModels")
sys.path.append("../Views")
import auto
import ocr

Flag_Image_Capture = False
FilePath="../../Images/image_capture/Image_screen.png"
CaptureHeight=100
CaptureWidth=100


#rootウィンドウを作成
root = tkinter.Tk()

OCR_Text=""
txt_ocr = tkinter.Label(root,text=OCR_Text)
txt_ocr.grid()

canvas = tkinter.Canvas(root,bg="#deb887", height=200,width=200)
canvas.grid()
global image_canvas

class ModifiedEntry(tkinter.Entry):
    EventName="<<TextModified>>"
    def __init__(self, *args, **kwargs):
        # Entry自体の初期化は元のクラスと同様。
        tkinter.Entry.__init__(self, *args, **kwargs)
        self.sv = tkinter.StringVar()
        # traceメソッドでStringVarの中身を監視。変更があったらvar_changedをコールバック
        self.sv.trace('w',self.var_changed)
        # EntryとStringVarを紐づけ。
        self.configure(textvariable = self.sv)
    
    # argsにはtrace発生元のVarの_nameが入っている
    # argsのnameと内包StringVarの_nameが一致したらイベントを発生させる。
    def var_changed(self, *args):
        if args[0] == self.sv._name:
            s = self.sv.get() 
            self.event_generate(self.EventName)

    def set_event_name(self, event_name):
        self.EventName
        self.EventName = event_name


def on_change(event):
    global FilePath
    FilePath = event.widget.get()
    
def on_change_capture_height(event):
    global CaptureHeight
    value = event.widget.get()
    if value=="":
        value="0"
    CaptureHeight = int(value)

def on_change_capture_width(event):    
    global CaptureWidth
    value = event.widget.get()
    if value=="":
        value="0"
    CaptureWidth = int(value)

          
def move(x, y):
    print('マウスポインターは {0} へ移動しました'.format((x, y)))

def click(x, y, button, pressed):
    global Flag_Image_Capture
    if Flag_Image_Capture == True:
        auto.Image_AroundMouse(file_path = FilePath ,wide=CaptureWidth , height=CaptureHeight)
        Flag_Image_Capture = False
        show_image()

    #if not pressed:     # クリックを離したら
    #    mouse_listener_stop()
    #    return False    # Listenerを止める

def scroll(x, y, dx, dy):
    print('{0} スクロールされた座標： {1}'.format(
        'down' if dy < 0 else 'up',(x, y)))

def on_pushed_capture():
    global Flag_Image_Capture
    Flag_Image_Capture = True

def on_pushed_ocr():
    # 画面Captureの文字認識
    ocr_instance = ocr.OCR()
    ocr_instance.Setting_BuilderText(6)
    OCR_Text = ocr_instance.Recognition_ByFilePath(FilePath, "jpn")
    print(OCR_Text)
    pyperclip.copy(OCR_Text)
    txt_ocr["text"]=OCR_Text

def on_change_ocr(event):    
    global OCR_Text
    value = event.widget.get()
    OCR_Test =value


def mouse_listener_stop():
    mouse_listener.stop()

def show_image():
    global image_canvas
    global canvas
    image_canvas=tkinter.PhotoImage(file=FilePath,width=200,height=200)
    canvas.create_image(0,0, image=image_canvas, anchor=tkinter.NW)
    
def make_window(title="Tkinterテスト",window_size="320x480",capture_label_text="label",capture_button_text="capture",ocr_button_text="ocr"):
    root.title(title)
    root.geometry(window_size)
    #Capture GUI
    capture_label = tkinter.Label(root, text=capture_label_text)
    capture_label.grid()

    txt = ModifiedEntry(root)
    #txt = tkinter.Entry(width=20)
    txt.grid()
    txt.bind("<<TextModified>>", on_change)
    #txt.place(x=90, y=70)
    txt.insert(tkinter.END,FilePath)

    txt_height = ModifiedEntry(root)
    txt_height.set_event_name("<<TextModified2>>")
    txt_height.grid()
    txt_height.bind("<<TextModified2>>", on_change_capture_height)
    txt_height.insert(tkinter.END,str(CaptureHeight))

    txt_width = ModifiedEntry(root)
    txt_width.set_event_name("<<TextModified3>>")
    txt_width.grid()
    txt_width.bind("<<TextModified3>>", on_change_capture_width)
    txt_width.insert(tkinter.END,str(CaptureWidth))


    capture_on_button = tkinter.Button(root, text=capture_button_text, command= lambda : on_pushed_capture())
    capture_on_button.grid()

    capture_on_button = tkinter.Button(root, text=ocr_button_text, command= lambda : on_pushed_ocr())
    capture_on_button.grid()

    
    #メインループ
    root.mainloop()

#mouse_listener = pynput.mouse.Listener(on_move=move, on_click=click,on_scroll=scroll)
mouse_listener = pynput.mouse.Listener(on_click=click) #,on_scroll=scroll)
mouse_listener.start()
make_window(capture_label_text="screen capture",capture_button_text="capture start")
