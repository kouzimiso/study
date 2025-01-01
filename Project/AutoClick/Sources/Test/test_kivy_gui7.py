import os
import kivy
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.event import EventDispatcher
from kivy.properties import StringProperty

def create_button(text, on_press):
    button = Button(text=text)
    button.bind(on_press=on_press)
    return button

class GenericPopup(Popup):
    def __init__(self, view_model, title, size_hint, buttons=None, **kwargs):
        super().__init__(**kwargs)
        self.view_model = view_model
        self.title = title
        self.size_hint = size_hint
        
        layout = BoxLayout(orientation='vertical')
        self.content_layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.content_layout)
        
        button_layout = BoxLayout(size_hint_y=None, height=50)
        if buttons:
            for btn_text, btn_callback in buttons:
                button_layout.add_widget(create_button(btn_text, btn_callback))
        button_layout.add_widget(create_button("Close", self.dismiss))
        layout.add_widget(button_layout)
        
        self.add_widget(layout)

    def set_content(self, widget):
        self.content_layout.clear_widgets()
        self.content_layout.add_widget(widget)
class FileChooserPopup(Popup):
    def __init__(self, view_model, **kwargs):
        def on_select(instance):
            if self.path_input.text:
                view_model.change_file_path(self.path_input.text)
                self.dismiss()

        def update_filer_path(instance, value):
            self.path_input.text = value

        super().__init__(
            title="Select a File",
            size_hint=(0.8, 0.8),
            **kwargs
        )

        # Create a layout for FileChooser and TextInput
        layout = BoxLayout(orientation='vertical')

        # Create and configure FileChooserListView
        self.filer = FileChooserListView(size_hint=(1, 0.8))
        directory_path = os.path.dirname(view_model.filer_path)
        if os.path.exists(directory_path):
            self.filer.path = directory_path

        # Create and configure TextInput
        self.path_input = TextInput(size_hint=(1, 0.1), height=30)
        self.path_input.bind(text=self.on_text_changed)
        view_model.bind(on_update_selected_path=update_filer_path)

        # Add widgets to the layout
        layout.add_widget(self.filer)
        layout.add_widget(self.path_input)

        # Add a select button
        select_button = Button(text="Select", size_hint=(1, 0.1))
        select_button.bind(on_press=on_select)
        layout.add_widget(select_button)

        # Add the layout to the popup
        self.add_widget(layout)

    def on_text_changed(self, instance, value):
        pass

class DictionaryKeyPopup(GenericPopup):
    def __init__(self, view_model, **kwargs):
        def on_select(instance):
            view_model.show_merge_popup(self.spinner.text)
            self.dismiss()

        keys = view_model.get_json_root_keys()
        super().__init__(
            view_model=view_model,
            title="Select Dictionary Root Key",
            size_hint=(0.5, 0.5),
            buttons=[("Select", on_select)],
            **kwargs
        )

        self.spinner = Spinner(text=keys[0], values=keys)
        self.set_content(self.spinner)

class MergeKeyPopup(GenericPopup):
    def __init__(self, view_model, original_key, **kwargs):
        def on_merge(instance):
            new_key = self.key_input.text
            value = view_model.read_data_dictionary.get(original_key, {})
            view_model.merge_to_data_dictionary(new_key, value)
            self.dismiss()

        def on_key_change(instance, value):
            self.check_key_duplicate(view_model.data_dictionary, value)

        super().__init__(
            view_model=view_model,
            title="Merge Key",
            size_hint=(0.6, 0.4),
            buttons=[("Merge", on_merge)],
            **kwargs
        )

        self.key_input = TextInput(text=original_key, multiline=False)
        self.key_input.bind(text=on_key_change)

        self.set_content(self.key_input)
        self.check_key_duplicate(view_model.data_dictionary, original_key)

    def check_key_duplicate(self, dictionary, key):
        if key in dictionary:
            self.key_input.background_color = (1, 0, 0, 1)  # Red for duplicate
        else:
            self.key_input.background_color = (1, 1, 1, 1)  # White for non-duplicate

class OverWritePopup(GenericPopup):
    def __init__(self, view_model, original_key, value, **kwargs):
        def on_overwrite(instance):
            view_model.merge_key_value(original_key, value, overwrite=True)
            self.dismiss()

        super().__init__(
            view_model=view_model,
            title="Key Overwrite",
            size_hint=(0.6, 0.4),
            buttons=[("Overwrite", on_overwrite)],
            **kwargs
        )

        self.set_content(Label(text=f"Key '{original_key}' already exists."))

class ViewModel(EventDispatcher):
    on_update_selected_path = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filer_path = ""
        self.data_dictionary = {}
        self.read_data_dictionary = {}

    def change_file_path(self, path):
        self.filer_path = path
        print(f"File path changed to: {path}")
        self.dispatch('on_update_selected_path', path)

    def get_json_root_keys(self):
        return ['key1', 'key2', 'key3']

    def show_merge_popup(self, key):
        print(f"Show merge popup for key: {key}")

    def merge_to_data_dictionary(self, new_key, value):
        self.data_dictionary[new_key] = value
        print(f"Data dictionary updated with key: {new_key}")

    def merge_key_value(self, key, value, overwrite=False):
        if overwrite or key not in self.data_dictionary:
            self.data_dictionary[key] = value
            print(f"Key '{key}' overwritten with value: {value}")

class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        view_model = ViewModel()
        
        btn_open_file = Button(text="Open File Chooser")
        btn_open_file.bind(on_press=lambda instance: FileChooserPopup(view_model).open())
        layout.add_widget(btn_open_file)
        
        btn_select_key = Button(text="Select Key")
        btn_select_key.bind(on_press=lambda instance: DictionaryKeyPopup(view_model).open())
        layout.add_widget(btn_select_key)
        
        return layout

if __name__ == '__main__':
    TestApp().run()
