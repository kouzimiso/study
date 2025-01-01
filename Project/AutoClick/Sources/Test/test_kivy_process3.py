import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import sys
# ローカルモジュールをインポート
sys.path.append("../Common")
sys.path.append("../Models")
sys.path.append("../ViewModels")
sys.path.append("../Views")
sys.path.append("./Common")
sys.path.append("./Models")
sys.path.append("./ViewModels")
sys.path.append("./Views")
sys.path.append("./Sources/Common")
sys.path.append("./Sources/Models")
sys.path.append("./Sources/ViewModels")
sys.path.append("./Sources/Views")

import TaskManager
#import kivy_ui 
class MyApp(App):
    def build(self):
        self.task_manager = TaskManager.TaskManager()
        
        layout = BoxLayout(orientation='vertical')
        
        self.label = Label(text='Press the button to start a task')
        layout.add_widget(self.label)
        
        button = Button(text='Start Background Task', size_hint=(1, 0.2))
        button.bind(on_press=self.start_task)
        layout.add_widget(button)
        
        return layout

    def start_task(self, instance):
        plan_name_list = "example_task"
        plan_lists = ["example_plan1", "example_plan2"]
        self.task_manager.run_test()
        self.label.text = 'Task started! Check console for output.'

if __name__ == '__main__':
    MyApp().run()
