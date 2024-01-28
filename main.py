import kivy

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.recycleview import RecycleView 
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle, Color
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.factory import Factory


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.count = 0
        self.active_data = {}
    
    def connect_bat(self, instance):
        self.ids.boxText.clear_widgets()
        self.count = 0

        self.ids.isConnectedLabel.text = u"Весы подключены"

        print("Bat connected")
        vp_height = self.ids.scrollText.viewport_size[1]
        sv_height = self.ids.scrollText.height
        
        for i in range(7):
            label = SingleFile(data = [i], size_hint=(1, None), height=50)
            self.ids.boxText.add_widget(label)
            
            self.count += 1



class MyApp(App):
    def build(self):
        return MainScreen()


class SingleFile(BoxLayout):
    data = ListProperty([])
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)


    def on_click_bat(self):
        print("data: " + str(self.data[0]))

        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Сохранить BAT", content=content,
                            size_hint=(0.9, 0.9))

        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def save(self, path, filename):
        self.dismiss_popup()
    

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


if __name__ == '__main__':
    MyApp().run()
