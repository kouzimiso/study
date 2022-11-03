from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from datetime import datetime


class MainWindow(Widget):
    button_text = StringProperty("Push Button!!")
    timer_text = StringProperty("START")

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.timer_check = False
        self.timer_before = 0

    def push_button(self):
        if not self.timer_check:
            self.timer_before = datetime.now()
            self.timer_check = True
            self.button_text = "STOP"
            self.timer_text = "Running..."
        else:
            self.timer_check = False
            self.button_text = "START"
            self.timer_text = str(datetime.now() - self.timer_before)


class StopWatchApp(App):
    def __init__(self, **kwargs):
        super(StopWatchApp, self).__init__(**kwargs)

    def build(self):
        return MainWindow()


if __name__ == '__main__':
    StopWatchApp().run()