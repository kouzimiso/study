from random import random
from kivy.app import App
from kivy.config import Config

Config.set("graphics", "width", "1024")
Config.set("graphics", "height", "768")
Config.set("graphics", "resizable", False)

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.properties import ObjectProperty
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.togglebutton import ToggleButton

from kivy.utils import get_color_from_hex
from kivy.core.window import Window


class MyPaintWidget(Widget):
    #pass
    last_color = "" 
    line_width = 3
    def on_touch_down(self, touch):
        if Widget.on_touch_down(self, touch):
            return
        with self.canvas:
            touch.ud["line"] = Line(points=(touch.x, touch.y), width=self.line_width)

    def set_line_width(self, line_width=3):
        self.line_width = line_width
    
    def on_touch_move(self, touch):
        if touch.ud:
            touch.ud["line"].points += [touch.x, touch.y]
    
    def set_color(self, new_color):
        self.last_color = new_color
        self.canvas.add(Color(*new_color))


class MyCanvasWidget(Widget):
    
    def clear_canvas(self):
        MyPaintWidget.clear_canvas(self)


class MyPaintApp(App):
    def __init__(self, **kwargs):
        super(MyPaintApp, self).__init__(**kwargs)
        self.title = "image display"
    
    def build(self):
        parent = Widget()
        self.painter = MyCanvasWidget()
        self.painter.ids["paint_area"].set_color(
            get_color_from_hex("#000000"))
        return self.painter

    def clear_canvas(self):
        self.painter.ids["paint_area"].canvas.clear()
        self.painter.ids["paint_area"].set_color(self.painter.ids["paint_area"].last_color)

    def save_canvas(self):
        Window.screenshot()

class ColorButton(ToggleButton):
    def _do_press(self):
        if self.state == "normal":
            ToggleButtonBehavior._do_press(self)

if __name__ == "__main__":
    Window.clearcolor = get_color_from_hex("#ffffff")
    MyPaintApp().run()
