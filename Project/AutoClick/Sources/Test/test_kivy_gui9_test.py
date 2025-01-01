import json
import asynckivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label

class Wizard:
    def __init__(self, plan_lists):
        self.plan_lists = plan_lists
        self.current_plan_list = 0
        self.data = {}

    def next_plan(self):
        if self.current_plan_list < len(self.plan_lists):
            plan_list = self.plan_lists[self.current_plan_list]
            if plan_list["type"] == "GUI":
                asynckivy.start(self.show_multiple_inputs(plan_list["settings"]))
            else:
                # 他のタイプの処理を非同期で実行する場合もasynckivy.startを使う
                asynckivy.start(self.process_other_plan(plan_list))
        else:
            print("All plan_lists completed!")

    async def show_multiple_inputs(self, settings):
        layout = BoxLayout(orientation='vertical')

        contents = settings.get("contents", [])
        for content in contents:
            if content["form"] == "get_file_path":
                self.add_file_path_input(layout, content)
            elif content["form"] == "get_text":
                self.add_text_input(layout, content)

        next_button = Button(text="Next")
        next_button.bind(on_release=lambda x: asynckivy.start(self.collect_data_and_proceed(contents)))
        layout.add_widget(next_button)

        popup = Popup(title="Input Data", content=layout, size_hint=(0.8, 0.8))
        self.popup = popup
        popup.open()

    def add_file_path_input(self, layout, content):
        text_input = TextInput(hint_text=content["comment"])
        file_button = Button(text="Select File")

        def open_file_chooser(instance):
            file_chooser_popup = self.create_file_chooser_popup(text_input)
            file_chooser_popup.open()

        file_button.bind(on_release=open_file_chooser)
        sub_layout = BoxLayout(orientation='horizontal')
        sub_layout.add_widget(text_input)
        sub_layout.add_widget(file_button)
        layout.add_widget(Label(text=content["comment"]))
        layout.add_widget(sub_layout)

        content["input_widget"] = text_input

    def add_text_input(self, layout, content):
        text_input = TextInput(hint_text=content["comment"])
        layout.add_widget(Label(text=content["comment"]))
        layout.add_widget(text_input)
        content["input_widget"] = text_input

    def create_file_chooser_popup(self, text_input):
        layout = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView()
        layout.add_widget(file_chooser)

        def on_selection(instance, selection):
            if selection:
                text_input.text = selection[0]
            popup.dismiss()

        select_button = Button(text='Select')
        select_button.bind(on_release=lambda instance: on_selection(instance, file_chooser.selection))
        layout.add_widget(select_button)

        popup = Popup(title="Choose File", content=layout, size_hint=(0.8, 0.8))
        return popup

    async def collect_data_and_proceed(self, contents):
        for content in contents:
            result_key = content["result_key"]
            input_widget = content.get("input_widget")

            if input_widget is not None:
                self.data[result_key] = input_widget.text
            else:
                print(f"Error: No widget found for {result_key}")

        self.popup.dismiss()
        self.current_plan_list += 1
        self.next_plan()

    async def process_other_plan(self, plan_list):
        if plan_list["settings"]["action"] == "merge_data":
            await self.merge_data()
        elif plan_list["settings"]["action"] == "close_window":
            await self.close_window()
        elif plan_list["action"] == "next_window":
            await self.next_window()

    async def merge_data(self):
        base_file_path = self.data.get("base_file_path")
        merge_file_path = self.data.get("merge_file_path")
        merge_key_value = self.data.get("merge_key_value")

        with open(base_file_path, 'r') as f:
            base_data = json.load(f)

        with open(merge_file_path, 'r') as f:
            merge_data = json.load(f)

        base_data[merge_key_value] = merge_data.get(merge_key_value)

        print(f"Merge completed: {base_data}")
        self.current_plan_list += 1
        self.next_plan()

    async def close_window(self):
        print("Window closed")
        self.current_plan_list += 1
        self.next_plan()

    async def next_window(self):
        print("Opening next window...")
        self.current_plan_list += 1
        self.next_plan()

def process_plan_list(wizard):
    # plan_listを処理するロジック
    wizard.next_plan()

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        start_button = Button(text='Start Wizard')
        start_button.bind(on_release=self.start_wizard)
        layout.add_widget(start_button)
        return layout

    def start_wizard(self, instance):
        plan_lists = [
            {
                "type": "GUI",
                "settings": {
                    "contents": [
                        {
                            "form": "get_file_path",
                            "result_key": "base_file_path",
                            "comment": "Please select base file path"
                        },
                        {
                            "form": "get_file_path",
                            "result_key": "merge_file_path",
                            "comment": "Please select merge file path"
                        }
                    ]
                }
            },
            {
                "type": "GUI",
                "settings": {
                    "contents": [
                        {
                            "form": "get_text",
                            "result_key": "merge_key_value",
                            "comment": "Please input key name to merge"
                        }
                    ]
                }
            },
            {
                "type": "GUI",
                "settings": {
                    "action": "merge_data"
                }
            },
            {
                "type": "GUI",
                "settings": {
                    "action": "close_window"
                }
            }
        ]

        wizard = Wizard(plan_lists)
        process_plan_list(wizard)

if __name__ == '__main__':
    MyApp().run()
