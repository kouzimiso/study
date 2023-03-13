import multiprocessing
from kivy.app import App
from kivy.uix.label import Label


class GUIProcess(multiprocessing.Process):
    def __init__(self, data, queue):
        super().__init__()
        self.data = data
        self.queue = queue

    def run(self):
        app = MyApp(self.data, self.queue)
        app.run()

class MyApp(App):
    def __init__(self, data, queue):
        super().__init__()
        self.data = data
        self.queue = queue

    def build(self):
        return Label(text="Hello World")

    def on_stop(self):
        self.queue.put(self.data)


class GUI:
    def run(self,data):
        result = {}
        queue = multiprocessing.Queue()
        process = GUIProcess(data, queue)
        process.start()
        process.join()
        result = queue.get()
        return result

    
if __name__ == '__main__':
    data = {"key": "value"}
    queue = multiprocessing.Queue()
    process = GUIProcess(data, queue)
    process.start()
    process.join()
    result = queue.get()
    print(result)


    data = {"key": "value"}
    result = {}
    process = GUI()
    result = process.run(data)
    print(result)

