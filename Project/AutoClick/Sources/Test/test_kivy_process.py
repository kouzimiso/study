# main.py
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
import multiprocessing
import threading
import time

def process_function():
    print("Process started")
    time.sleep(5)
    print("Process finished")

def thread_function():
    print("Thread started")
    time.sleep(5)
    print("Thread finished")

class MyApp(App):
    def start_process(self, *args):
        process = multiprocessing.Process(target=process_function)
        process.start()

    def start_thread(self, *args):
        thread = threading.Thread(target=thread_function)
        thread.start()

    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        process_button = Button(text='Start Process')
        process_button.bind(on_press=self.start_process)
        layout.add_widget(process_button)

        thread_button = Button(text='Start Thread')
        thread_button.bind(on_press=self.start_thread)
        layout.add_widget(thread_button)

        return layout

if __name__ == '__main__':
    MyApp().run()
