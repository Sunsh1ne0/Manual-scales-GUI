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
import time

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo  import ZoneInfo

import pyuac

TIMEZONE = ZoneInfo("Iceland")

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
        self._block_status = False

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
            
            # self.temporary = self.ard
            
            cmd_error, self.files_amount, self._block_status = self.ard.Init()
            # print(self.files_amount)
            # print(self._block_status)
            # print(cmd_error)
            if self._block_status:
                grid = BoxLayout()
                self.ids.boxlay.clear_widgets()
                self.ids.isConnectedLabel.text = u"Необходима разблокировка"
                self.ids.connect.disabled = True
                self.ids.boxlay.add_widget(grid)
                text_space = TextInput(text=f"")
                text_space.hint_text = u"Введите пароль"
                grid.add_widget(text_space)
                unblock_btn = Button(text=u"Разблокировать")
                # print(text_space.text)
                unblock_btn.bind(on_press = lambda x: self.unblock_cmd(text_space.text))
                grid.add_widget(unblock_btn)
            else:

                self.ids.isConnectedLabel.text = u"Весы подключены"
                self.ids.connect.disabled = True
                self.ids.date_time.disabled = False
                
                if (self.files_amount != 0):
                    error_list, self.files = self.ard.File_Info(self.files_amount)
                    print(f"errors: {error_list}")
                    print(self.files)
                    self.ids.boxText.clear_widgets()
                    vp_height = self.ids.scrollText.viewport_size[1]
                    sv_height = self.ids.scrollText.height
                    for message in self.files:
                        label = SingleFile(message, self.ard, self)
                        self.ids.boxText.add_widget(label)
                        # text_space = Label(text=f"File: {message['file']}, Weightings: {message['lines'] - 2}, Time: {datetime.datetime.fromtimestamp(message['unix'], tz=ZoneInfo("Atlantic/Reykjavik"))}") #, tz=ZoneInfo("Europe/London")
                        text_space = Label(text=f"File: {message['name']}, Weightings: {message['lines'] - 2}, Time: {datetime.datetime.fromtimestamp(message['unix']).astimezone(TIMEZONE)}") #, tz=ZoneInfo("Europe/London")

                        # text_space = Label(text=f"File: {message['file']}")
                        label.add_widget(text_space)
                else:
                    self.ids.boxText.padding = 20
                    self.ids.boxText.clear_widgets()
                    text_space = Label(text=u"Нет файлов")
                    self.ids.boxlay.add_widget(text_space)
        except SerialException:
            self.ids.isConnectedLabel.text = u"Весы не обнаружены"
            # print(u"N")
            # self.connect_bat()

        
    def unblock_cmd(self, pwd):
        try:
            int(pwd)
        except:
            pwd = 0000
        print(int(pwd))
        _, st = self.ard.Unblock_Scales(int(pwd))
        if (st):
            self._block_status = True
            self.ids.boxlay.clear_widgets()
            self.ids.boxlay.add_widget(Label(text=u"Весы успешно разблокированы"))


    def set_time(self, instance):
        print(self.ard.Set_Time())
        

class MyApp(App):
    def build(self):
        return MainScreen()


class SingleFile(BoxLayout):
    def __init__(self, data, arduino, main_window, **kwargs):
        super(SingleFile, self).__init__(**kwargs)
        self.height = 50
        self.size_hint = (1, None)
        self.temp_arr = []
        self.arduino = arduino
        self.temp = data
        self.main_window = main_window



    def on_click_bat(self):
        messages, error_list = self.arduino.Get_File(self.temp['file'], self.temp['lines'])
        
        self.temp_arr = []

        for message in messages:
            self.temp_arr.append(message)

        content = SaveDialog(save=self.save_bat, text_input = self.temp['name'], cancel=self.dismiss_popup)
        content.ids.text_input.hint_text = self.temp['name']

        self._popup = Popup(title="Сохранить BAT", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def on_click_csv(self):
        messages, error_list = self.arduino.Get_File(self.temp['file'], self.temp['lines'])

        print(messages)

        self.temp_arr = []

        for message in messages:
            self.temp_arr.append(message)
                
        self.data = pd.DataFrame(self.temp_arr, index=np.linspace(1, self.temp['lines'] - 2, self.temp['lines'] - 2))
        self.data = self.data.reset_index(drop=True)
        self.data["Weight"] = self.data["Weight"].apply(lambda x: x / 1000)
        self.data["SavedDateTime"] = self.data["SavedDateTime"].apply(lambda x: datetime.datetime.fromtimestamp(x).astimezone(TIMEZONE))
        
        self.data.drop(columns='ID', inplace=True)
        content = SaveDialog(save=self.save_csv, cancel=self.dismiss_popup)
        content.ids.text_input.hint_text = self.temp['name']
        # content.ids.text_input.text = self.temp['name']
        self._popup = Popup(title="Сохранить CSV", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def delete_file(self):
        self.arduino.Delete_File(self.temp['file'])
        self.disabled = True
        self.main_window.ids.boxText.remove_widget(self)

    def dismiss_popup(self):
        self._popup.dismiss()

    def save_csv(self, path, filename):
        if filename == '':
            filename = self.temp['name']
        filepath = path + "/" + filename + ".csv"
        self.data.to_csv(filepath, sep=';')
        self.dismiss_popup()

    def save_bat(self, path, filename):
        symb = "\ "
        if filename == '':
            filename = self.temp['name']
        if (path[-1] != symb[0]) or (path[-1] != '/'):
            path += symb[0]
        origin_path = create_blank_db(path)
        add_weightings_table(path)
        add_file_table(path, 0, filename)
        for data in self.temp_arr:
            add_samples_table(path, data['WeighingId'], data['Weight'] / 1000.0, data['Flag'], get_julian_datetime(datetime.datetime.fromtimestamp(data['SavedDateTime']).astimezone(TIMEZONE)))
        save_db_in_file(path, filename, origin_path)
        self.dismiss_popup()
    

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


def main():

    #if hasattr(sys, '_MEIPASS'):
    #    resource_add_path(os.path.join(sys._MEIPASS))
    MyApp().run()
    #else:
    #    exit()


if __name__ == '__main__':
    if not pyuac.isUserAdmin():
        print("Re-launching as admin!")
        pyuac.runAsAdmin()
    else:        
        main()  