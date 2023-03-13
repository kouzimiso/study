import sys
import multiprocessing
import kivy
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock

class CloseGUI(kivy.uix.boxlayout.BoxLayout):
    def __init__(self, **kwargs):
        super(CloseGUI, self).__init__(**kwargs)
        # アプリケーションを開始したときに呼び出される
        Clock.schedule_once(self.close_GUI, 0.1) # 0.1秒後にclose_appを呼び出す

    def close_GUI(self, *args):
        # アプリケーションを終了する
        App.get_running_app().stop()
        Window.close()
        print("on_request_close")        
        
class CloseApp(App):
    def __init__(self):
        super().__init__()
        kivy.core.window.Window.size = (100, 20)

    def build(self):
        return CloseGUI()
    
class DialogGUI(BoxLayout):
    def __init__(self, data, **kwargs):
        print("GUI init")
        super(DialogGUI, self).__init__(**kwargs)
        self.add_widget(kivy.uix.label.Label(text=data))
        kivy.core.window.Window.bind(on_request_close=self.on_request_close)
        
    def on_request_close(self, *args):
        # ウィンドウを閉じる
        App.get_running_app().stop()
        kivy.core.window.Window.close()
        print("on_request_close")
        return True

class DialogApp(App):
    def __init__(self,data,queue):
        print("App init")
        super().__init__()
        self.data = data
        self.queue =queue
        kivy.core.window.Window.size = (300, 500)

    def build(self):
        #Window.borderless = True
        return DialogGUI(self.data)

    def on_pause(self):
        # バックグラウンドに回るときにデータを返す
        return self.data

    def on_stop(self):
        self.queue.put(self.data)

class DialogProcess(multiprocessing.Process):
    def __init__(self, data, queue):
        super().__init__()
        self.data = data
        self.queue = queue
        print("Process init")

    def run(self):
        print("GUI run")
        app = DialogApp(self.data, self.queue)
        app.run()
        

class Dialog:
    def run(self,data):
        print("Dialog run")
        queue = multiprocessing.Queue()
        process = DialogProcess(data, queue)
        print("Dialog start")
        process.start()
        print("Dialog join")
        process.join()
        print("queue.get")
        queue = queue.get()
        return queue

def main():
    data = "Hello World"
    dialog=Dialog()
    result=dialog.run(data)
    print(result)

    dialog=Dialog()
    result=dialog.run(data)
    print(result)
    
    dialog=Dialog()
    result=dialog.run(data)
    print(result)

gui=CloseApp()
gui.run()
if __name__ == "__main__":
    sys.exit(main())
