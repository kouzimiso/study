from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
import json
import os


class SchemaWidget(BoxLayout):
    def __init__(self, schema, data=None, **kwargs):
        super().__init__(orientation='vertical', spacing=5, size_hint_y=None, **kwargs)
        self.schema = schema
        self.data = data or {}
        self.widgets = {}
        self.build_from_schema(schema, self.data)
        self.bind(minimum_height=self.setter('height'))

    def build_from_schema(self, schema, data=None, key_prefix=''):
        data = data or {}
        # Resolve $ref first
        if '$ref' in schema:
            ref_path = schema['$ref']
            if ref_path.startswith('#/$defs/'):
                def_name = ref_path.split('/')[-1]
                defs = self.schema.get('$defs', {})
                schema = defs.get(def_name, {})
        schema_type = schema.get('type')

        if schema_type == 'object':
            properties = schema.get('properties', {})
            for prop_key, prop_schema in properties.items():
                full_key = f"{key_prefix}.{prop_key}" if key_prefix else prop_key
                prop_value = data.get(prop_key, None)
                box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
                box.bind(minimum_height=box.setter('height'))
                label_text = prop_key
                if 'description' in prop_schema:
                    label_text += f" ({prop_schema['description']})"
                box.add_widget(Label(text=label_text + ':', font_size=16, size_hint_y=None, height=30))
                # Recursively resolve nested $ref if present
                if '$ref' in prop_schema:
                    ref_path = prop_schema['$ref']
                    if ref_path.startswith('#/$defs/'):
                        def_name = ref_path.split('/')[-1]
                        defs = self.schema.get('$defs', {})
                        prop_schema = defs.get(def_name, {})
                # Recursively build nested schema
                widget = self.build_from_schema(prop_schema, prop_value, full_key)
                box.add_widget(widget)
                self.add_widget(box)
                self.widgets[full_key] = widget

            additional = schema.get('additionalProperties', True)
            if additional:
                add_button = Button(text='Add new field', size_hint_y=None, height=40)
                def on_add_new_field(instance):
                    new_key = f"new_key_{len(self.widgets)}"
                    new_prop_schema = schema.get('additionalProperties', {"type": "string"})
                    if not isinstance(new_prop_schema, dict):
                        new_prop_schema = {"type": "string"}
                    new_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
                    new_box.bind(minimum_height=new_box.setter('height'))
                    label = Label(text=new_key + ':', font_size=16, size_hint_y=None, height=30)
                    widget = self.build_from_schema(new_prop_schema, None, new_key)
                    new_box.add_widget(label)
                    new_box.add_widget(widget)
                    self.add_widget(new_box)
                    self.widgets[new_key] = widget
                    self.height = sum(getattr(child, 'height', 0) for child in self.children) + self.spacing * len(self.children) + 10
                add_button.bind(on_release=on_add_new_field)
                self.add_widget(add_button)
            self.height = sum(getattr(child, 'height', 0) for child in self.children) + self.spacing * len(self.children) + 10
            return self

        elif schema_type == 'array':
            container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
            container.bind(minimum_height=container.setter('height'))
            items_schema = schema.get('items', {})
            values = data if isinstance(data, list) else []

            self.array_items = []
            for idx, item_data in enumerate(values):
                item_widget = SchemaWidget(items_schema, item_data)
                container.add_widget(item_widget)
                self.array_items.append(item_widget)

            add_btn = Button(text='Add item', size_hint_y=None, height=40)
            def add_item(instance):
                new_item = SchemaWidget(items_schema)
                container.add_widget(new_item)
                self.array_items.append(new_item)
                container.height = sum(child.height + container.spacing for child in container.children) + 10
            add_btn.bind(on_release=add_item)
            container.add_widget(add_btn)
            container.height = sum(child.height + container.spacing for child in container.children) + 10
            return container

        elif schema_type == 'string':
            text = data if isinstance(data, str) else ''
            ti = TextInput(text=text, multiline=False, size_hint_y=None, height=40, font_size=16)
            return ti

        elif schema_type == 'integer':
            text = str(data) if isinstance(data, int) else ''
            ti = TextInput(text=text, multiline=False, size_hint_y=None, height=40, font_size=16, input_filter='int')
            return ti

        elif schema_type == 'number':
            text = str(data) if isinstance(data, (int, float)) else ''
            ti = TextInput(text=text, multiline=False, size_hint_y=None, height=40, font_size=16, input_filter='float')
            return ti

        elif schema_type == 'boolean':
            # Represent boolean as text input with 'true' or 'false'
            text = str(data).lower() if isinstance(data, bool) else ''
            ti = TextInput(text=text, multiline=False, size_hint_y=None, height=40, font_size=16)
            return ti

        else:
            # Fallback TextInput for unknown types
            text = str(data) if data is not None else ''
            ti = TextInput(text=text, multiline=False, size_hint_y=None, height=40, font_size=16)
            return ti

    def get_data(self):
        # Recursively gather data from widgets
        def gather(schema, widget, key_prefix=''):
            schema_type = schema.get('type')
            if schema_type == 'object':
                result = {}
                properties = schema.get('properties', {})
                for prop_key, prop_schema in properties.items():
                    full_key = f"{key_prefix}.{prop_key}" if key_prefix else prop_key
                    child_widget = self.widgets.get(full_key)
                    if child_widget:
                        val = gather(prop_schema, child_widget, full_key)
                        if val is not None:
                            result[prop_key] = val
                return result

            elif schema_type == 'array':
                items_schema = schema.get('items', {})
                values = []
                # widget is a BoxLayout with items and add button at end
                for child in widget.children:
                    # Skip the add button which is a Button instance
                    if isinstance(child, Button):
                        continue
                    if isinstance(child, SchemaWidget):
                        val = child.get_data()
                        values.append(val)
                    elif isinstance(child, BoxLayout):
                        # In case items are wrapped in BoxLayout (unlikely here)
                        pass
                values.reverse()  # because Kivy children are in reverse order
                return values

            elif schema_type in ['string', 'integer', 'number', 'boolean']:
                if isinstance(widget, TextInput):
                    text = widget.text.strip()
                    if schema_type == 'integer':
                        try:
                            return int(text)
                        except:
                            return None
                    elif schema_type == 'number':
                        try:
                            return float(text)
                        except:
                            return None
                    elif schema_type == 'boolean':
                        if text.lower() in ['true', '1', 'yes']:
                            return True
                        elif text.lower() in ['false', '0', 'no']:
                            return False
                        else:
                            return None
                    else:
                        return text
                else:
                    return None
            else:
                # Unknown type fallback
                if isinstance(widget, TextInput):
                    return widget.text.strip()
                return None

        return gather(self.schema, self)


class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)

        # Load file input
        load_btn = Button(text='Load JSON File', size_hint_y=None, height=40)
        load_btn.bind(on_release=self.open_filechooser)
        self.add_widget(load_btn)

        # Save file button
        save_btn = Button(text='Save JSON File', size_hint_y=None, height=40)
        save_btn.bind(on_release=self.save_json)
        self.add_widget(save_btn)

        # Container for schema-based input
        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)

        self.schema_widget = None
        self.current_schema = None
        self.current_data = None

    def open_filechooser(self, *_):
        content = FileChooserIconView()
        popup = Popup(title='Select JSON file', content=content, size_hint=(0.9, 0.9))

        def on_file_select(instance, selection, touch):
            if selection:
                path = selection[0]
                popup.dismiss()
                self.load_json_file(path)

        content.bind(on_submit=on_file_select)
        popup.open()

    def load_json_file(self, path):
        if not os.path.isfile(path):
            print("JSON file path is none."+path)
            return
        if os.path.getsize(path) == 0:
            print("JSON file is empty.")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f'Error loading JSON file: {e}')
            return

        # Expect the JSON to have a 'schema' and optionally 'data' keys
        schema = data.get('schema')
        input_data = data.get('data', {})

        if not schema:
            print("No schema found in JSON file.")
            return

        self.current_schema = schema
        self.current_data = input_data

        # Clear old content
        self.content.clear_widgets()

        # Build UI from schema
        self.schema_widget = SchemaWidget(schema, input_data)
        self.content.add_widget(self.schema_widget)

    def save_json(self, *_):
        if not self.schema_widget or not self.current_schema:
            print("No schema loaded.")
            return

        data = self.schema_widget.get_data()

        # Save to file dialog
        content = FileChooserIconView(select_string='Save', path='.')
        popup = Popup(title='Save JSON file', content=content, size_hint=(0.9, 0.9))

        def on_save(instance, selection):
            if selection:
                path = selection[0]
                popup.dismiss()
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump({'schema': self.current_schema, 'data': data}, f, ensure_ascii=False, indent=2)
                    print(f'Saved to {path}')
                except Exception as e:
                    print(f'Error saving JSON file: {e}')

        content.bind(on_submit=on_save)
        popup.open()


class JsonSchemaEditorApp(App):
    def build(self):
        return RootWidget()


if __name__ == '__main__':
    JsonSchemaEditorApp().run()