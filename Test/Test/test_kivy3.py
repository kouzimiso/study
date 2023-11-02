# coding:utf-8

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.uix.widget import Widget
from kivy.core.text import LabelBase,DEFAULT_FONT
from kivy.resources import resource_add_path
#from kivy.lang import Builder

from kivy.config import Config
from kivy.properties import StringProperty

resource_add_path('./fonts')
#kivy.core.text.LabelBase.register(kivy.core.text.DEFAULT_FONT,'mplus-2c-regular.ttf')
LabelBase.register(DEFAULT_FONT,'mplus-2c-regular.ttf')

Config.set('graphics','width',640)
Config.set('graphics','height',480)
Config.set('graphics','resizable',1)

class TextWidget(Widget):
    pass

#class MainScreen(BoxLayout):
#    def __init__(self, **kwargs):
#        super(self).__init__(**kwargs)
        #btn = Button(text="btn")
        #self.add_widget(btn)

class MainApp(App):
    source = StringProperty('../../Images/image_capture/Image_screen.png')
    def __init__(self, **kwargs):
        super(MainApp,self).__init__(**kwargs)
        self.title="greeting"

    def build(self):
        #MS = MainScreen()
        #return MS
        
        return TextWidget()

if __name__=="__main__":
    MainApp().run()
