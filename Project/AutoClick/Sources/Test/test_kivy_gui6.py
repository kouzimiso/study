import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label


class Wizard:
    def __init__(self, steps):
        self.steps = steps
        self.current_step = 0
        self.data = {}

    def start(self):
        self.process_step()

    def process_step(self):
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            
            if step["type"] == "GUI":
                if "contents" in step["settings"]:
                    self.show_multiple_inputs(step["settings"]["contents"])
                elif step["action"] == "merge_data":
                    self.merge_data()
                elif step["action"] == "close_window":
                    self.close_window()
                elif step["action"] == "next_window":
                    self.next_window()
        else:
            print("All steps completed!")

    def show_multiple_inputs(self, contents):
        layout = BoxLayout(orientation='vertical')

        for content in contents:
            if content["form"] == "get_file_path":
                self.add_file_path_input(layout, content)
            elif content["form"] == "get_text":
                self.add_text_input(layout, content)

        next_button = Button(text="Next")
        next_button.bind(on_release=lambda x: self.collect_data_and_proceed(contents))
        layout.add_widget(next_button)

        popup = Popup(title="Input Data", content=layout, size_hint=(0.8, 0.8))
        self.popup = popup  # popupをインスタンス変数として保持
        popup.open()

    def add_file_path_input(self, layout, content):
        text_input = TextInput(hint_text=content["comment"])
        file_button = Button(text="Select File")

        def open_file_chooser(instance):
            file_chooser_popup = self.create_file_chooser_popup(text_input)
            file_chooser_popup.open()

        file_button.bind(on_release=open_file_chooser)
        layout.add_widget(Label(text=content["comment"]))
        layout.add_widget(text_input)
        layout.add_widget(file_button)

        # Store the TextInput and result_key for later data collection
        content["input_widget"] = text_input  # 正しくウィジェットを保存

    def add_text_input(self, layout, content):
        text_input = TextInput(hint_text=content["comment"])
        layout.add_widget(Label(text=content["comment"]))
        layout.add_widget(text_input)
        content["input_widget"] = text_input  # 正しくウィジェットを保存

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

    def collect_data_and_proceed(self, contents):
        for content in contents:
            result_key = content["result_key"]
            input_widget = content.get("input_widget")

            if input_widget is not None:
                self.data[result_key] = input_widget.text  # 入力値をデータとして保存
            else:
                print(f"Error: No widget found for {result_key}")

        self.popup.dismiss()  # 入力完了後にポップアップを閉じる
        self.current_step += 1
        self.process_step()

    def merge_data(self):
        base_file_path = self.data.get("base_file_path")
        merge_file_path = self.data.get("merge_file_path")
        merge_key_value = self.data.get("merge_key_value")

        with open(base_file_path, 'r') as f:
            base_data = json.load(f)

        with open(merge_file_path, 'r') as f:
            merge_data = json.load(f)

        # 指定されたキーでマージ
        base_data[merge_key_value] = merge_data.get(merge_key_value)

        # マージ結果の出力や処理
        print(f"Merge completed: {base_data}")
        self.current_step += 1
        self.process_step()

    def close_window(self):
        print("Window closed")
        self.current_step += 1
        self.process_step()

    def next_window(self):
        print("Opening next window...")
        self.current_step += 1
        self.process_step()


class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        start_button = Button(text='Start Wizard')
        start_button.bind(on_release=self.start_wizard)
        layout.add_widget(start_button)
        return layout

    def start_wizard(self, instance):
        steps = [
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
                            "result_key": "merge_key_name",
                            "comment": "Please input key name to merge"
                        }
                    ]
                }
            },
            {
                "type": "GUI",
                "action": "merge_data"
            },
            {
                "type": "GUI",
                "action": "close_window"
            }
        ]
        wizard = Wizard(steps)
        wizard.start()


if __name__ == '__main__':
    MyApp().run()
