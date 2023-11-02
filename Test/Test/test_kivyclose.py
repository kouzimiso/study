import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window

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

if __name__ == '__main__':
    CloseApp().run() # アプリケーションを実行する
