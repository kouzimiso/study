from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class NestedStackLayoutApp(App):
    def vertical_layout(self):
        inner_layout2 = StackLayout(size_hint_y=None)
        label10 = Label(text='Box V0', size_hint=(None, None), size=(200, 25))
        label11 = Label(text='Box V1', size_hint=(None, None), size=(200, 25))
        label12 = Label(text='Box V2', size_hint=(None, None), size=(200, 25))
        label13 = Label(text='Box V3', size_hint=(None, None), size=(200, 25))
        label14 = Label(text='Box V4', size_hint=(None, None), size=(200, 25))
        label15 = Label(text='Box V5', size_hint=(None, None), size=(200, 25))
        label16 = Label(text='Box V6', size_hint=(None, None), size=(200, 25))
        inner_layout2.add_widget(label10)
        inner_layout2.add_widget(label11)
        inner_layout2.add_widget(label12)
        inner_layout2.add_widget(label13)
        inner_layout2.add_widget(label14)
        inner_layout2.add_widget(label15)
        inner_layout2.add_widget(label16)
        return inner_layout2

    def add_label(self,layout,text):
        label1 = Label(text=text+' 1', size_hint=(None, None), size=(50, 25))
        label2 = Label(text=text+' 2', size_hint=(None, None), size=(50, 25))
        label3 = Label(text=text+' 3', size_hint=(None, None), size=(50, 25))
        label4 = Label(text=text+' 4', size_hint=(None, None), size=(50, 25))
        label5 = Label(text=text+' 5', size_hint=(None, None), size=(50, 25))
        label6 = Label(text=text+' 6', size_hint=(None, None), size=(50, 25))
        layout.add_widget(label1)
        layout.add_widget(label2)
        layout.add_widget(label3)
        layout.add_widget(label4)
        layout.add_widget(label5)
        layout.add_widget(label6)
        return layout
    
    def build(self):
        outer_layout = MyBoxLayout()
        layout = self.create_layout()
        return outer_layout
    
    def create_layout(self):
        inner_vertical_layout1=self.vertical_layout()
        inner_vertical_layout2=self.vertical_layout()
        inner_vertical_layout1.add_widget(inner_vertical_layout2)
        inner_vertical_layout3=self.vertical_layout()
        inner_vertical_layout1.add_widget(inner_vertical_layout3)

        inner_layout1 = BoxLayout(orientation="horizontal")
        text = "BoxLayout_horizon1"
        inner_layout1=self.add_label(inner_layout1,text)

        inner_layout2 = BoxLayout(orientation="horizontal")
        text = "BoxLayout_horizon2"
        inner_layout2=self.add_label(inner_layout2,text)
        inner_layout1.add_widget(inner_layout2)

        inner_layout3 = BoxLayout(orientation="horizontal")
        text = "BoxLayout_horizon2"
        inner_layout3 = self.add_label(inner_layout3,text)
        inner_layout1.add_widget(inner_layout3)

        inner_layout4 = MyBoxLayout()
        inner_layout1.add_widget(inner_layout4)
        # 外側のStackLayout
        outer_layout = BoxLayout(size_hint=(None, None))
        outer_layout.add_widget(inner_vertical_layout1)
        outer_layout.add_widget(inner_layout1)
        
        return outer_layout

class MyBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MyBoxLayout, self).__init__(**kwargs)
        # BoxLayoutのorientationをverticalに設定
        self.orientation = 'vertical'
        self.valign='top'
        # 縦に配置するLabelを追加
        for i in range(3):
            label = Label(text=f'Label {i+1}')
            self.add_widget(label)
        
        # 横に配置するBoxLayoutを作成し、中にLabelを追加
        horizontal_box = BoxLayout(orientation='horizontal')
        for i in range(3):
            label = Label(text=f'Label {i+4}')
            horizontal_box.add_widget(label)
        # 横に配置したBoxLayoutを親BoxLayoutに追加
        self.add_widget(horizontal_box)


        # 縦に配置するLabelを追加
        vertical_box = BoxLayout(orientation='vertical',valign='top')

        for i in range(3):
            label = Label(text=f'Label {i+7}')
            vertical_box.add_widget(label)
        horizontal_box.add_widget(vertical_box)

if __name__ == '__main__':
    NestedStackLayoutApp().run()
