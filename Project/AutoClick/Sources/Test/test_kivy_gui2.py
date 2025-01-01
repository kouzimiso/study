from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder

Builder.load_string('''
<MyBoxLayout>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: 0, 0, 1, 0.5
        Rectangle:
            size: self.size
            pos: self.pos
<TestBoxLayout>:
    ScrollView:
        do_scroll_x: False
        size_hint_y: None
        height: self.parent.height
        BoxLayout:
            id: test_layout
    
            size_hint_y: None
            height: self.minimum_height
            canvas.before:
                Color:
                    rgba: 0, 0, 1, 0.5
                Rectangle:
                    size: self.size
                    pos: self.pos
''')

class TestBoxLayout(BoxLayout):
    def __init__(self, text="",color="white",**kwargs):
        super(TestBoxLayout, self).__init__(**kwargs)
        self.size_hint=(None,None)
        x,y=self.pos
        width,height = self.size


        label1 = Label(text=text +' x:'+str(x),color=color, size_hint=(None, None), halign="left", padding=(0, 0),height=30)
        label2 = Label(text=text +' y:'+str(y),color=color, size_hint=(None, None), halign="left", padding=(0, 0),height=30)
        label3 = Label(text=text +' width:'+str(width),color=color, size_hint=(None, None), halign="left", padding=(0, 0),height=30)
        label4 = Label(text=text +' height:'+str(height),color= color, size_hint=(None, None), halign="left", padding=(0, 0),height=30)

        label1.size_hint_x = 0.2  # 幅の割合を設定
        label2.size_hint_x = 0.2
        label3.size_hint_x = 0.3
        label4.size_hint_x = 0.3
        test_layout = self.ids.test_layout
        self.add_widget(label1)
        self.add_widget(label2)
        test_layout.add_widget(label3)
        test_layout.add_widget(label4)
        for  i in range(12):
            label_i = Label(text=text + str(i)+ ' x:'+str(x),color=color, size_hint=(None, None), halign="left", padding=(0, 0),height=30+i)
            self.add_widget(label_i)


        self.minimum_height = self.get_size(self)
        self.height = self.minimum_height
        #with self.canvas.before:
        #    Color(0, 0, 1, 0.5)
        #    self.rect = Rectangle(pos=self.pos, size=self.size)

    #def update_canvas(self, *args):
    #    self.rect.size = self.size
    #    self.rect.pos = self.pos
    def get_size(self,widget):
        total_height = 0
        for widget_children in widget.children:
            if isinstance(widget_children, (Button, Label,TextInput)) :
                total_height += widget_children.height 
            elif isinstance(widget_children, BoxLayout) or isinstance(widget_children, ScrollView):
                total_height += widget_children.height
                for item in widget_children.children:
                    total_height += self.get_size(item)
        return total_height
        


class MyBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MyBoxLayout, self).__init__(**kwargs)

        vertical_layout1 = TestBoxLayout("vertical1","red", orientation='vertical')
        horizontal_layout = TestBoxLayout("horizontal1","yellow", orientation='horizontal')
        vertical_layout2 = TestBoxLayout("vertical2", orientation='vertical')
        vertical_layout3 = TestBoxLayout("vertical3", orientation='vertical')
        vertical_layout4 = TestBoxLayout("vertical4", orientation='vertical')

        self.add_widget(vertical_layout1)
        self.add_widget(horizontal_layout)
        self.add_widget(vertical_layout2)
        self.add_widget(vertical_layout3)
        self.add_widget(vertical_layout4)

class MyApp(App):
    def build(self):
        return MyBoxLayout()

if __name__ == '__main__':
    MyApp().run()
