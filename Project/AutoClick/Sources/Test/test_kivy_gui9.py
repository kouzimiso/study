import json
import asynckivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner

# GUI_Form handles the display and interaction for the various form elements in the app
class GUI_Form:
    def __init__(self, wizard):
        # Store a reference to the Wizard object and initialize the popup attribute
        self.wizard = wizard
        self.popup = None

    # Show multiple input fields as defined in the `settings` dictionary
    async def show_multiple_inputs(self, settings):
        layout = BoxLayout(orientation='vertical')  # Create a vertical layout for the popup

        # Iterate through the contents to add various input fields
        contents = settings.get("contents", [])
        for content in contents:
            if content["form"] == "get_file_path":
                self.add_file_path_input(layout, content)  # Add file path input field
            elif content["form"] == "get_text":
                self.add_text_input(layout, content)  # Add text input field
            elif content["form"] == "select_dictionary_key":
                await self.add_dictionary_key_input(layout, content)  # Add key selection field

        # Create a "Next" button to proceed to the next step
        next_button = Button(text="Next")
        next_button.bind(on_release=lambda x: asynckivy.start(self.collect_data_and_proceed(contents)))
        layout.add_widget(next_button)

        # Create and display the popup
        popup = Popup(title="Input Data", content=layout, size_hint=(0.8, 0.8))
        self.popup = popup
        popup.open()

    # Add a file path input field and a button to open the file chooser
    def add_file_path_input(self, layout, content):
        text_input = TextInput(hint_text=content["comment"])  # Text field for file path input
        file_button = Button(text="Select File")  # Button to open file chooser

        # Open the file chooser when the button is pressed
        def open_file_chooser(instance):
            file_chooser_popup = self.create_file_chooser_popup(text_input)
            file_chooser_popup.open()

        file_button.bind(on_release=open_file_chooser)  # Bind button to the file chooser event
        sub_layout = BoxLayout(orientation='horizontal')  # Layout for the text field and button
        sub_layout.add_widget(text_input)
        sub_layout.add_widget(file_button)
        layout.add_widget(Label(text=content["comment"]))  # Add label above the input
        layout.add_widget(sub_layout)

        content["input_widget"] = text_input  # Store the text input widget for later use

    # Add a simple text input field to the layout
    def add_text_input(self, layout, content):
        text_input = TextInput(hint_text=content["comment"])  # Text field for user input
        layout.add_widget(Label(text=content["comment"]))  # Label for the input
        layout.add_widget(text_input)
        content["input_widget"] = text_input  # Store the text input widget for later use

    # Add a spinner input field for selecting a dictionary key
    async def add_dictionary_key_input(self, layout, content):
        # Load the dictionary from the specified file path
        file_path = self.wizard.data.get(content["reference"]["dictionary_file_path"])
        with open(file_path, 'r') as f:
            dictionary_data = json.load(f)

        keys = list(dictionary_data.keys())  # Extract dictionary keys
        spinner = Spinner(text="Select Key", values=keys)  # Create a dropdown for the keys

        layout.add_widget(Label(text=content["comment"]))  # Label for the input
        layout.add_widget(spinner)

        content["input_widget"] = spinner  # Store the spinner widget for later use

    # Create a popup with a FileChooser to select a file
    def create_file_chooser_popup(self, text_input):
        layout = BoxLayout(orientation='vertical')  # Vertical layout for the file chooser
        file_chooser = FileChooserListView()  # File chooser widget
        layout.add_widget(file_chooser)

        # Handle file selection and set the file path to the text_input field
        def on_selection(instance, selection):
            if selection:
                text_input.text = selection[0]
            popup.dismiss()  # Close the popup

        # Create a "Select" button to confirm file selection
        select_button = Button(text='Select')
        select_button.bind(on_release=lambda instance: on_selection(instance, file_chooser.selection))
        layout.add_widget(select_button)

        popup = Popup(title="Choose File", content=layout, size_hint=(0.8, 0.8))  # Create the popup
        return popup

    # Collect data from the input fields and proceed to the next step
    async def collect_data_and_proceed(self, contents):
        for content in contents:
            result_key = content["result_key"]
            input_widget = content.get("input_widget")

            # Retrieve the input from the widget and store it in the wizard's data
            if input_widget is not None:
                self.wizard.data[result_key] = input_widget.text
            else:
                print(f"Error: No widget found for {result_key}")

        self.popup.dismiss()  # Close the current popup
        self.wizard.next_plan()  # Move to the next plan in the wizard

# Wizard manages the steps (plans) of the process and holds data across steps
class Wizard:
    def __init__(self, plan_lists):
        self.plan_lists = plan_lists  # List of plans to process
        self.current_plan_list = 0  # Track the current step
        self.data = {}  # Store data collected during the wizard process
        self.form = GUI_Form(self)  # GUI_Form instance to handle user input

    # Move to the next step in the plan
    def next_plan(self):
        self.current_plan_list += 1
        self.process_plan()  # Process the next plan

    # Process the current plan in the plan list
    def process_plan(self):
        if self.current_plan_list < len(self.plan_lists):
            plan_list = self.plan_lists[self.current_plan_list]
            if plan_list["type"] == "GUI":
                asynckivy.start(self.form.show_multiple_inputs(plan_list["settings"]))  # Show form
            elif plan_list["type"] == "dictionary_merge":
                self.dictionary_merge(plan_list)  # Merge dictionaries
        else:
            print("All plan_lists completed!")  # All plans have been processed

    # Merge dictionary data from two files based on a specified key
    def dictionary_merge(self, plan_list):
        reference = plan_list["settings"]["reference"]
        base_file_path = self.data.get(reference["base_file_path"])
        merge_file_path = self.data.get(reference["merge_file_path"])
        merge_key = self.data.get(reference["merge_key"])
        new_merge_key = self.data.get(reference["new_merge_key"])

        # Load the base and merge dictionaries
        with open(base_file_path, 'r') as f:
            base_data = json.load(f)
        with open(merge_file_path, 'r') as f:
            merge_data = json.load(f)

        # Add the data from the merge dictionary under the new key in the base dictionary
        base_data[new_merge_key] = merge_data.get(merge_key)

        # Write the updated base dictionary back to the file
        with open(base_file_path, 'w') as f:
            json.dump(base_data, f, indent=4)

        print(f"Merge completed: {base_data}")  # Print merge result for confirmation
        self.next_plan()  # Move to the next plan

# Start the wizard process
def process_plan_list(wizard):
    wizard.process_plan()

# Kivy app class to manage the GUI
class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')  # Main layout for the app
        start_button = Button(text='Start Wizard')  # Button to start the wizard
        start_button.bind(on_release=self.start_wizard)  # Bind the button to start the wizard
        layout.add_widget(start_button)
        return layout

    # Start the wizard with predefined plan lists
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
                            "form": "select_dictionary_key",
                            "result_key": "merge_key",
                            "comment": "Please select key to merge",
                            "reference": {
                                "dictionary_file_path": "merge_file_path"
                            }
                        },
                        {
                            "form": "get_text",
                            "result_key": "new_merge_key",
                            "comment": "Please input name to merge.If the field is blank, the system will use a key to merge.",
                            "reference": {
                                "empty_default_value": "merge_key"
                            }
                        }
                    ]
                }
            },
            {
                "type": "dictionary_merge",
                "settings": {
                    "reference": {
                        "base_file_path": "base_file_path",
                        "merge_file_path": "merge_file_path",
                        "merge_key": "merge_key",
                        "new_merge_key": "new_merge_key"
                    }
                }
            }
        ]

        wizard = Wizard(plan_lists)  # Initialize the wizard with the plan list
        process_plan_list(wizard)  # Start processing the plan list

# Entry point for the Kivy app
if __name__ == '__main__':
    MyApp().run()
