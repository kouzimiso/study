from multiprocessing import Process, Manager
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

def kivy_app_process(data_dict):
    class MyApp(App):
        def build(self):
            layout = BoxLayout(orientation='vertical')
            button = Button(text='Click me')
            button.bind(on_press=lambda x: self.update_data(data_dict))
            layout.add_widget(button)
            return layout

        def update_data(self, data_dict):
            data_dict['count'] += 1
            print(f"Data updated: {data_dict}")

    MyApp().run()

if __name__ == '__main__':
    with Manager() as manager:
        data_dict = manager.dict({'count': 0})
        p = Process(target=kivy_app_process, args=(data_dict,))
        p.start()
        p.join()
        print(f"Final data: {data_dict}")
        data_dict = manager.dict({'count': 0})
        p = Process(target=kivy_app_process, args=(data_dict,))
        p.start()
        p.join()
        print(f"Final data: {data_dict}")
    
