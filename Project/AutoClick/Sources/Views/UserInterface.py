import sys
import multiprocessing
from kivy.app import App
from kivy.lang.builder import Builder
#from kivy.logger import Logger
import kivy
#from kivy.uix.label import Label
#from kivy.uix.boxlayout import BoxLayout
#from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.clock import Clock

sys.path.append("../Common")
sys.path.append("../../Common")

import dictionaryeditor_kivy
import FunctionUtility

class CloseGUI(kivy.uix.boxlayout.BoxLayout):
    def __init__(self, **kwargs):
        super(CloseGUI, self).__init__(**kwargs)
        # アプリケーションを開始したときに呼び出される
        Clock.schedule_once(self.close_GUI, 0.1) # 0.1秒後にclose_appを呼び出す

    def close_GUI(self, *args):
        # アプリケーションを終了する
        App.get_running_app().stop()
        Window.close()
        print("on_request_close")        
        
class CloseApp(App):
    def __init__(self):
        super().__init__()
        kivy.core.window.Window.size = (100, 20)

    def build(self):
        return CloseGUI()
    
#multiprocessingでkivy Appを起動し、辞書データを渡して編集後に辞書データを戻す
class EditorProcess(multiprocessing.Process):
    def __init__(self, data, queue):
        super().__init__()
        self.data = data
        self.queue = queue

    def run(self):
        app = dictionaryeditor_kivy.EditorApp(self.data, self.queue)
        app.run()
        

class DictionaryEditor:
    def run(self,data):
        queue = multiprocessing.Queue()
        process = EditorProcess(data, queue)
        process.start()
        print("join")
        process.join()
        print("queue.get")
        queue = queue.get()
        print("return")
        return queue

class ValueEditor:
    def run(self, data):
        if type(data) == dict:
            self.data = data
            dictionary_to_value =False
        else:
            self.data = {"value":data}
            dictionary_to_value =True
        
        queue = multiprocessing.Queue()
        process = EditorProcess(self.data, queue)
        process.start()
        process.join()
        queue = queue.get()
        if dictionary_to_value == True:
            return queue["value"]
        else:
            return queue

def main(argument_dictionary):
    print("test")
    
    editor = DictionaryEditor()
    print("test")
    result = editor.run(argument_dictionary)
    print(result)

    editor = DictionaryEditor()
    result = editor.run(argument_dictionary)
    print(result)

    argument_dictionary = "test"
    editor = ValueEditor()
    result = editor.run(argument_dictionary)
    print(result)


if __name__ == "__main__":
    gui=CloseApp()
    gui.run()
    # Defaultの辞書Data
    default_dictionary = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4'
    }
    argument_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    main(argument_dictionary)
