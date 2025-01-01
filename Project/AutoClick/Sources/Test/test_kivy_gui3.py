from kivy.app import App
from kivy.uix.boxlayout import BoxLayout


class RootWidget(BoxLayout):
    pass


class Test_Kivy_Gui3App(App):
    def build(self):
        return RootWidget()


if __name__ == '__main__':
    Test_Kivy_Gui3App().run()