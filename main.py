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
import new_sqlite_bat_process
import datetime
import os


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

    example_data = []

    def on_click_bat(self):
        print("data: " + str(self.data[0]))
        # ToDo: 
        # Get data file number self.data[0] from arduino 
        self.example_data = [{"time": 1, "val": 1, "category": 1}, {"time": 2, "val": 2, "category": 2}, {"time": 3, "val": 3, "category": 3}]
        # end todo
        

        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Сохранить BAT", content=content,
                            size_hint=(0.9, 0.9))

        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def save(self, path, filename):
        filepath = path + "/" + "Export.b1d"
        new_sqlite_bat_process.create_blank_db(filepath)
        new_sqlite_bat_process.add_file_table(filepath, len(self.example_data))
        for i in range(0, len(self.example_data)):
            time = datetime.datetime.fromtimestamp(self.example_data[i]["time"])
            new_sqlite_bat_process.add_samples_table(filepath, i, self.example_data[i]["val"], self.example_data[i]["category"], time)

        zip_filepath = path + "/" + filename + '.b1e'
        new_sqlite_bat_process.save_db_in_file(filepath, zip_filepath)
        try:
            os.remove(filepath)
        except Exception:
            pass

        self.dismiss_popup()
    

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


if __name__ == '__main__':
    MyApp().run()
