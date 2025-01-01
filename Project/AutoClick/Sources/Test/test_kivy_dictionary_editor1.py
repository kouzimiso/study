import sys
import multiprocessing
from kivy.app import App
from kivy.lang.builder import Builder
#from kivy.logger import Logger
import kivy
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.clock import Clock
    
class EditorGUI(kivy.uix.boxlayout.BoxLayout):
    def __init__(self, data, **kwargs):
        print("GUI init")
        super(EditorGUI, self).__init__(**kwargs)
        self.data = data
        self.padding = 20
        self.orientation = 'vertical'
        print("GUI listup")
        # kvファイルで定義されたリストを読み込み、動的にウィジェットを作成
        for key, value in self.data.items():
            print("List up")
            self.add_widget(Label(text=key))
            self.add_widget(TextInput(text=value))

        ## 更新ボタンを作成
        btn = Button(text='Update')
        btn.bind(on_press=self.update_data)
        self.add_widget(btn)

        # 終了ボタンを作成
        #btn = Button(text='Close Window')
        #btn.bind(on_press=self.close)
        #self.add_widget(btn)
        
        # ウィンドウ終了時のイベントにon_request_closeをバインド
        kivy.core.window.Window.bind(on_request_close=self.on_request_close)
    '''
    def update_data(self,obj):
        # 辞書データを更新
        for i in range(0, len(self.children), 2):
            if i+1 >= len(self.children):
                break
            key = self.children[i].text
            value = self.children[i+1].text
            self.data[key] = value
        # コンソールに辞書データを表示
        print(self.data)
    '''
    def update_data(self,obj):
        # 辞書データを更新
        key = ""
        value =""
        for child in self.children:
            if isinstance(child, Label):
                key = child.text
            if isinstance(child, TextInput):
                value = child.text
                self.data[key] = value
        # コンソールに辞書データを表示
        print(self.data)

    
    def on_request_close(self, *args):
        # ウィンドウを閉じる
        App.get_running_app().stop()
        kivy.core.window.Window.close()
        print("on_request_close")
        # Trueを返すことでウィンドウを閉じることを許可する
        return True

class EditorApp(App):
    def __init__(self, data, queue):
        super().__init__()
        self.data = data
        self.queue = queue
        kivy.core.window.Window.size = (300, 400)

    def build(self):
        #Window.borderless = True
        return EditorGUI(self.data)

    def on_pause(self):
        # バックグラウンドに回るときに辞書データを更新して返す
        return self.data

    def on_stop(self):
        #Logger.critical('App: Aaaargh I\'m dying!')
        self.queue.put(self.data)

class EditorProcess(multiprocessing.Process):
    def __init__(self, data, queue):
        super().__init__()
        self.data = data
        self.queue = queue

    def run(self):
        app = EditorApp(self.data, self.queue)
        app.run()
        return self.queue
        

def main():

    data = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4'
    }
    print("test")
    queue =multiprocessing.Queue()
    editor = EditorProcess(data,queue)
    print("test")
    result = editor.run()
    print("test")
    print(result)

    editor = EditorProcess(data,queue)
    result = editor.run()
    print(result)

    data ="test"
    editor = EditorProcess()
    result = editor.run(data,queue)
    print(result)

if __name__ == "__main__":
    sys.exit(main())
