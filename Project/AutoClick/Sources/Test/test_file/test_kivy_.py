# coding:utf-8

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        btn = Button(text="btn")
        self.add_widget(btn)

class MainApp(App):
    def build(self):
        MS = MainScreen()
        return MS

if __name__=="__main__":
    MainApp().run()
