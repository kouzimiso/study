from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.event import EventDispatcher
import kivy_ui

Builder.load_string('''
<LoadButton>:
    size_hint: None, None
    size: 100, 50

<RecursionEditor>:
    orientation: 'vertical'
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: 'vertical'
            id: editor_layout
''')


class LoadButton(Button):
    def callback(self, path):
        self.parent.load_page(path)


class RecursionEditor(BoxLayout):
    current_path = []

    def __init__(self, dictionary, observer, **kwargs):
        super().__init__(**kwargs)
        self.dictionary = dictionary
        self.observer = observer
        self.create_ui(dictionary)

    def create_ui(self, dictionary, path=[]):
        editor_layout = self.ids.editor_layout
        editor_layout.clear_widgets()

        # Display path
        if path and len(path) > 0:
            path_str = '/'.join(path)
            path_label = Label(text=path_str)
            up_button = LoadButton(text='[up]')
            up_button.bind(on_press=lambda instance: self.load_page(path[:-1]))
            sub_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
            sub_layout.add_widget(path_label)
            sub_layout.add_widget(up_button)
            editor_layout.add_widget(sub_layout)

        # Display dictionary contents
        for key, value in dictionary.items():
            if isinstance(value, dict):
                sub_button = LoadButton(text=f'[{key}]')
                sub_button.bind(on_press=lambda instance, key=key: self.load_page(path+[key]))
                editor_layout.add_widget(sub_button)
            elif isinstance(value, list):
                sub_layout = BoxLayout(orientation='horizontal')
                label = Label(text=f'{key}:')
                sub_layout.add_widget(label)
                for i, item in enumerate(value):
                    sub_input = kivy_ui.ValueInput(value=item)
                    sub_layout.add_widget(sub_input)
                    sub_input.bind(text=lambda instance, value, k=key, i=i: self.on_text_change(path[-1], k, i, value))
                editor_layout.add_widget(sub_layout)
            else:
                # Add key-value pair horizontally
                sub_layout = BoxLayout(orientation='horizontal')
                label = Label(text=f'{key}:')
                sub_layout.add_widget(label)
                text_input = kivy_ui.ValueInput(value = value)
                text_input.bind(text=lambda instance, value, k=key: self.on_text_change(path[-1], k, None, value))
                sub_layout.add_widget(text_input)
                editor_layout.add_widget(sub_layout)

    def load_page(self, path):
        self.current_path = path
        sub_dict = self.dictionary
        for key in self.current_path:
            if isinstance(sub_dict, dict):  # sub_dictが辞書型かどうかをチェック
                sub_dict = sub_dict.get(key, {})  # 辞書型であればsub_dict[key]にアクセス
            else:
                sub_dict = {}  # 辞書型でなければ空の辞書を代入して続行
        self.create_ui(sub_dict, path)

    def on_text_change(self, path, key, index, value):
        current_dict = self.dictionary
        if path is not list:
            path = [path]
        for part in path:
            current_dict = current_dict[part]

        if index is not None:
            current_dict[key][index] = value
        else:
            current_dict[key] = value

        self.observer.dispatch('on_change', self.dictionary)


class Observer(EventDispatcher):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_change')
        Clock.schedule_interval(self.check_changes, 1)
        self.observers = []

    def check_changes(self, dt):
        pass  # Do nothing

    def on_change(self, dictionary):
        for observer in self.observers:
            observer.update_data(dictionary)

    def add_observer(self, observer):
        self.observers.append(observer)


class DataDisplay(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_display = kivy_ui.ValueInput(value='', readonly=True, multiline=True)
        self.add_widget(self.text_display)

    def update_data(self, dictionary):
        data_text = "\n".join([f"{key}: {value}" for key, value in dictionary.items()])
        self.text_display.text = data_text


class DictionaryApp(App):
    def build(self):
        root_layout = BoxLayout(orientation='horizontal')
        dictionary = {
            'data1': {
                'name': 'John',
                'age': 30,
                'friends': ['Alice', 'Bob', 'Charlie'],
                'details': {
                    'height': 180,
                    'weight': 75
                }
            },
            'data2': {
                'name': 'John',
                'age': 30,
                'friends': ['Alice', 'Bob', 'Charlie']
            }
        }
        observer = Observer()
        data_display = DataDisplay()
        data_display.update_data(dictionary)
        observer.add_observer(data_display)
        editor = RecursionEditor(dictionary, observer)
        root_layout.add_widget(editor)
        root_layout.add_widget(data_display)
        return root_layout


if __name__ == '__main__':
    DictionaryApp().run()
