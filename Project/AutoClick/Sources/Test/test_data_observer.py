from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.properties import StringProperty

class Data:
    """データクラス"""
    def __init__(self):
        self._value = ""
        self._observers = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._value != new_value:
            self._value = new_value
            self.notify_observers()

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer()

class Observer:
    """Observerクラス"""
    def __init__(self, data):
        self.data = data

    def __call__(self):
        self.update(self.data.value)

    def update(self, value):
        pass

class MyObserver(Observer):
    """具体的なObserver"""
    def __init__(self, data):
        super(MyObserver, self).__init__(data)

    def update(self, value):
        self.data.value = value

class MyWidget(BoxLayout):
    """GUIウィジェット"""
    def __init__(self, data, **kwargs):
        super(MyWidget, self).__init__(**kwargs)
        self.data = data
        self.text_input = TextInput()
        self.text_input.bind(text=self.on_text)
        self.add_widget(self.text_input)

    def on_text(self, instance, value):
        self.data.value = value

class MyApp(App):
    """Kivyアプリケーション"""

    def build(self):
        self.title = 'Observer Pattern Example'
        data = Data()
        for _ in range(2):
            observer = MyObserver(data)
            data.add_observer(observer)
        layout = BoxLayout(orientation='vertical')
        for _ in range(2):
            widget = MyWidget(data)
            layout.add_widget(widget)
        # データの値を表示するラベルを追加
        label = Label(text=data.value)
        layout.add_widget(label)
        # データの値が変更されたときにラベルのテキストを更新するObserverを登録
        label_observer = Observer(data)
        label_observer.update = lambda value: setattr(label, 'text', value)
        data.add_observer(label_observer)
        return layout

if __name__ == '__main__':
    MyApp().run()
