from kivy.app import App
from kivy.uix.label import Label


class ScreenApp(App):
    def __init__(self, data_dict):
        super().__init__()
        self.data_dict = data_dict

    def build(self):
        label = Label(text=str(self.data_dict['counter']))
        return label
