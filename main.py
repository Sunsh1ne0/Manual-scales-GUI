from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.recycleview import RecycleView 
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.factory import Factory

from Terminal_class import arduino
from db import create_blank_db, add_file_table, add_samples_table, add_weightings_table, get_julian_datetime, save_db_in_file

from serial.serialutil import SerialException
import pandas as pd
import numpy as np
import datetime
import serial.tools.list_ports


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.count = 0
        self.active_data = {}
        self.files_amount = None
        self.files = {}
        self.temp_arr= []
        self.file = None
        self.fileID = 5
        self.port = None

        self.ard = None
       
    
    def connect_bat(self, instance):
        try:
            ports = list(serial.tools.list_ports.comports())
            for port in ports:
                if "CH340" in port.description:
                    self.port = port.device
            if self.port == None:
                raise SerialException
            self.ard = arduino(self.port, 115200)
            self.ids.isConnectedLabel.text = u"Весы подключены"
            # self.temporary = self.ard
            
            cmd_error, self.files_amount = self.ard.Init()
            print(self.files_amount)
            if (self.files_amount != 0):
                error_list, self.files = self.ard.File_Info(self.files_amount)
                print(f"errors: {error_list}")
                print(self.files)

                self.ids.connect.disabled = True
                self.ids.date_time.disabled = False
                self.ids.boxText.clear_widgets()
                vp_height = self.ids.scrollText.viewport_size[1]
                sv_height = self.ids.scrollText.height
                for message in self.files:
                    label = SingleFile(message, self.ard)
                    self.ids.boxText.add_widget(label)
                    text_space = Label(text=f"File: {message['file']}, Weightings: {message['lines']}, Time: {datetime.datetime.fromtimestamp(message['unix'])}")
                    label.add_widget(text_space)
                    # self.ids.i.Label.text = "f"
                    # self.ids.i.text = "d"
                    
                    # self.count += 1
            else:
                self.ids.boxText.clear_widgets()
                text_space = Label(text=u"Нет файлов")
                self.ids.boxText.add_widget(text_space)
        except SerialException:
            self.ids.isConnectedLabel.text = u"Весы не обнаружены"
            print("No connection")

        

    def set_time(self, instance):
        print(self.ard.Set_Time())
        None



class MyApp(App):
    def build(self):
        return MainScreen()


class SingleFile(BoxLayout):
    def __init__(self, data, arduino, **kwargs):
        super(SingleFile, self).__init__(**kwargs)
        self.height = 50
        self.size_hint = (1, None)
        self.temp_arr = []
        self.arduino = arduino
        self.temp = data



    def on_click_bat(self):
        messages, error_list = self.arduino.Get_File(self.temp['file'], self.temp['lines'])

        for message in messages:
            self.temp_arr.append(message)

        content = SaveDialog(save=self.save_bat, cancel=self.dismiss_popup)
        self._popup = Popup(title="Сохранить BAT", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def on_click_csv(self):
        messages, error_list = self.arduino.Get_File(self.temp['file'], self.temp['lines'])

        for message in messages:
            self.temp_arr.append(message)
                
        self.data = pd.DataFrame(self.temp_arr, index=np.linspace(1, self.temp['lines'], self.temp['lines']))
        self.data = self.data.reset_index(drop=True)
        self.data["Weight"] = self.data["Weight"].apply(lambda x: x / 1000)
        self.data["SavedDateTime"] = self.data["SavedDateTime"].apply(lambda x: datetime.datetime.fromtimestamp(x))
        self.data.drop(columns='ID', inplace=True)
        content = SaveDialog(save=self.save_csv, cancel=self.dismiss_popup)
        self._popup = Popup(title="Сохранить CSV", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def save_csv(self, path, filename):
        filepath = path + "/" + filename + ".csv"
        self.data.to_csv(filepath, sep=';')
        self.dismiss_popup()

    def save_bat(self, path, filename):
        origin_path = create_blank_db(path)
        add_weightings_table(path)
        add_file_table(path, 0)
        for data in self.temp_arr:
            add_samples_table(path, data['WeighingId'], data['Weight'] / 1000.0, data['Flag'], get_julian_datetime(datetime.datetime.fromtimestamp(data['SavedDateTime'])))
        save_db_in_file(path, filename, origin_path)
        self.dismiss_popup()
    

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


if __name__ == '__main__':
    MyApp().run()
