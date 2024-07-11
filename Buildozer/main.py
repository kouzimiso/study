from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView

class FormItemApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        layout.add_widget(Label(text='FileChooserListView:'))
        filechooser = FileChooserListView()
        layout.add_widget(filechooser)

        layout.add_widget(Label(text='TextInput:'))
        layout.add_widget(TextInput(hint_text='Enter text here'))

        layout.add_widget(Label(text='CheckBox:'))
        layout.add_widget(CheckBox())

        layout.add_widget(Label(text='Switch:'))
        layout.add_widget(Switch())

        layout.add_widget(Label(text='Slider:'))
        slider = Slider(min=0, max=100, value=25)
        layout.add_widget(slider)
        
        layout.add_widget(Label(text='Spinner:'))
        spinner = Spinner(
            text='Option 1',
            values=('Option 1', 'Option 2', 'Option 3', 'Option 4'))
        layout.add_widget(spinner)

        layout.add_widget(Label(text='Button:'))
        layout.add_widget(Button(text='Click me'))

        layout.add_widget(Label(text='ToggleButton:'))
        layout.add_widget(ToggleButton(text='Toggle me'))

        layout.add_widget(Label(text='ProgressBar:'))
        progress_bar = ProgressBar(value=50, max=100)
        layout.add_widget(progress_bar)


        return layout

if __name__ == '__main__':
    FormItemApp().run()
