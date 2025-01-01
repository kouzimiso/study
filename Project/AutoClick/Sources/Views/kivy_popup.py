import sys
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
sys.path.append("./Sources/Common")
sys.path.append("./Sources/Models")
sys.path.append("./Sources/ViewModels")
sys.path.append("./Sources/Views")
import SharedMemory

class InputPopup(Popup):
    def __init__(self, shared_memory_name ,key_name , **kwargs):
        super(InputPopup, self).__init__(**kwargs)
        self.shared_memory_name = shared_memory_name
        self.key_name = key_name
        self.layout = BoxLayout(orientation='vertical')
        self.text_input = TextInput(hint_text='Enter your input here', multiline=False)
        self.submit_button = Button(text='Submit', on_press=self.submit)

        self.layout.add_widget(self.text_input)
        self.layout.add_widget(self.submit_button)
        
        self.content = self.layout

    def submit(self, instance):
        # ユーザーの入力を共有メモリに保存
        SharedMemory.write_key_to_shared_memory(self.shared_memory_name,self.key_name, self.text_input.text)
        self.dismiss()  # ポップアップを閉じる
        App.get_running_app().stop()

class MyApp(App):
    def __init__(self,shared_memory_name ,key_name, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.shared_memory_name = shared_memory_name
        self.key_name = key_name

    def build(self):
        # ポップアップを表示
        popup = InputPopup(self.shared_memory_name,self.key_name)
        popup.open()  # ポップアップを開く

        return self.root  # 空のウィジェットを返す

if __name__ == '__main__':
    shared_memory_name = "shared_memory.dat"
    key_name = "user_input"
    MyApp(shared_memory_name,key_name).run()
