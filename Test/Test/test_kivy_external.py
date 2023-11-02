import multiprocessing as mp
from kivy.app import App
from kivy.uix.label import Label


class MyApp(App):
    def __init__(self, counter):
        super().__init__()
        self.counter = counter

    def build(self):
        label = Label(text=str(self.counter))
        return label


def start_app(counter):
    app = MyApp(counter=counter)
    app.run()


if __name__ == '__main__':
    processes = []
    for i in range(3):
        p = mp.Process(target=start_app, args=(i,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
