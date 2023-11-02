import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window


class FileList(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.files = sorted(os.listdir('.'))

        self.file_buttons = []
        for file in self.files:
            button = Button(text=file, size_hint_y=None, height=50)
            button.bind(on_press=self.select_file)
            self.file_buttons.append(button)
            self.add_widget(button)

        self.selected_button = None

    def select_file(self, button):
        if self.selected_button is not None:
            self.selected_button.background_color = (1, 1, 1, 1)
        button.background_color = (0, 1, 0, 1)
        self.selected_button = button

    def move_up(self):
        if self.selected_button is not None:
            index = self.file_buttons.index(self.selected_button)
            if index > 0 and self.can_swap(index - 1):
                self.swap_files(index, index - 1)

    def move_down(self):
        if self.selected_button is not None:
            index = self.file_buttons.index(self.selected_button)
            if index < len(self.file_buttons) - 1 and self.can_swap(index):
                self.swap_files(index, index + 1)

    def can_swap(self, index):
        filename1 = self.files[self.file_buttons.index(self.selected_button)]
        filename2 = self.files[index]
        return filename1.split('_')[1] == filename2.split('_')[1]

    def swap_files(self, index1, index2):
        filename1 = self.files[index1]
        filename2 = self.files[index2]
        os.rename(filename1, self.get_new_filename(filename2))
        os.rename(filename2, self.get_new_filename(filename1))
        self.files[index1], self.files[index2] = self.files[index2], self.files[index1]
        self.file_buttons[index1], self.file_buttons[index2] = self.file_buttons[index2], self.file_buttons[index1]
        self.remove_widget(self.file_buttons[index1])
        self.insert_widget(index2, self.file_buttons[index1])

    def get_new_filename(self, filename):
        parts = filename.split('_')
        number_parts = parts[1].split('-')
        number_parts[1] = str(int(number_parts[1]) + 1)
        parts[1] = '-'.join(number_parts)
        return '_'.join(parts)


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        self.file_list = FileList()
        self.add_widget(self.file_list)

        button_layout = Box
