import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd
import numpy as np
import serial.tools.list_ports
from serial.serialutil import SerialException
import os

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from Terminal_class import arduino
from db import create_blank_db, add_file_table, add_samples_table, add_weightings_table, get_julian_datetime, save_db_in_file
import pyuac
import locale

current_locale = locale.getdefaultlocale()

language = current_locale[0].split('_')[0] 


TIMEZONE = ZoneInfo("Iceland")
# bg_color_app = "#daffc2"
# bg_color_app = "#bae89b"
bg_color_app = "#FFFFFF"
# bg_color_dark = "#bae89b"
bg_color_dark = "#daffc2"
# bg_color_dark = "grey"
# bg_color_light = "#e5fad7"
bg_color_light = "#FFFFFF"

bg_color_grey = "#e3e4e6"

fonts = [
            "Arial", "Arial Black", "Comic Sans MS", "Courier New", "Georgia", "Impact",
            "Lucida Console", "Lucida Sans Unicode", "Microsoft Sans Serif", "Palatino Linotype",
            "Segoe Print", "Segoe Script", "Segoe UI", "Tahoma", "Times New Roman", 
            "Trebuchet MS", "Verdana", "Webdings", "Wingdings", "Wingdings 2", "Wingdings 3"
        ]

class MainScreen(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.count = 0
        self.active_data = {}
        self.files_amount = None
        self.files = {}
        self.temp_arr = []
        self.file = None
        self.fileID = 5
        self.port = None
        self._block_status = False
        self.ard = None
        self.check_alive()
        self.create_widgets()

    def check_alive(self):
        ports = list(serial.tools.list_ports.comports())
        existing_port = None
        for port in ports:
            if "CH340" in port.description:
                existing_port = port
        if existing_port is None:
            if self.ard:
                self.disconnect_bat()
        self.after(100, self.check_alive)

    def create_widgets(self):
        self.main_layout = tk.Frame(self)
        self.main_layout.pack(fill=tk.BOTH, expand=True)

        self.top_frame = tk.Frame(self.main_layout, pady=10, background=bg_color_app)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        app_font = fonts[3]
        buttons_style = ttk.Style()
        buttons_style.configure("My.TButton",          # имя стиля
                            font=(app_font, 12),    # шрифт
                            foreground="#000000",   # цвет текста
                            # padding=10,             # отступы
                            background=bg_color_app)   # фоновый цвет
        
        label_style = ttk.Style()
        label_style.configure("My.TLabel",          # имя стиля
                            font=(app_font, 12),    # шрифт
                            foreground="#000000",   # цвет текста
                            padding=10, background=bg_color_app)

        self.top_frame_btn1 = ttk.Label(self.top_frame, anchor='w', background=bg_color_app)
        self.top_frame_btn1.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.connect_button = ttk.Button(self.top_frame_btn1, text=text_lang("Подключить весы", "Connect to scales", language), command=self.connect_bat, style="My.TButton", width=18)
        self.connect_button.pack(side=tk.LEFT, padx=5, expand=True)

        self.top_frame_btn2 = ttk.Label(self.top_frame, anchor='w', background=bg_color_app)
        self.top_frame_btn2.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.date_time_button = ttk.Button(self.top_frame_btn2, text=text_lang("Установить время", "Set time", language), command=self.set_time, style="My.TButton", width=18)
        self.date_time_button.pack(side=tk.LEFT, padx=5, expand=True)
        self.date_time_button.config(state=tk.DISABLED)

        self.top_frame_label = ttk.Label(self.top_frame, anchor='w', background=bg_color_app)
        self.top_frame_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.is_connected_label = ttk.Label(self.top_frame_label, text=text_lang("Весы не подключены", "Scales are not connected", language), anchor='center', style="My.TLabel", width=28)
        self.is_connected_label.pack(expand=True)

        self.middle_frame = tk.Frame(self.main_layout, pady=10, background=bg_color_app)
        self.middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.boxlay = tk.Frame(self.middle_frame, relief=tk.SUNKEN, borderwidth=1, background=bg_color_app)
        self.boxlay.pack(fill=tk.BOTH, expand=True)

        self.scroll_text = tk.Canvas(self.boxlay, background=bg_color_light)
        self.scroll_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.boxlay, orient="vertical", command=self.scroll_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

        self.scroll_text.configure(yscrollcommand=self.scrollbar.set)

        self.box_text = tk.Frame(self.scroll_text, background=bg_color_light)
        self.scroll_text.create_window((0, 0), window=self.box_text, anchor='nw', tags="box_text_window")

        # Bind the resize event of box_text to update the scroll region
        self.box_text.bind("<Configure>", self.update_scrollregion)

        self.scroll_text.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scroll_text.bind_all("<Shift-MouseWheel>", self._on_shiftmouse)
        self.scroll_text.bind_all("<Button-4>", self._on_mousewheel)  # For macOS compatibility
        self.scroll_text.bind_all("<Button-5>", self._on_mousewheel)  # For macOS compatibility
        
        self.boxlay.bind("<Configure>", self.on_frame_resized)

    def on_frame_resized(self, event):
        canvas_width = event.width
        items = self.scroll_text.find_withtag("box_text_window")
        if items:
            self.scroll_text.itemconfig(items[0], width=canvas_width)

    def _on_mousewheel(self, event):
        if event.delta:
            self.scroll_text.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            self.scroll_text.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_text.yview_scroll(1, "units")

    def _on_shiftmouse(self, event):
        self.scroll_text.xview_scroll(int(-1*(event.delta/120)), "units")

    def update_scrollregion(self, event):
        self.scroll_text.update_idletasks()  # Make sure the canvas is updated before checking the scroll region
        self.scroll_text.configure(scrollregion=self.scroll_text.bbox("all"))

        canvas_height = self.scroll_text.winfo_height()
        scroll_region_height = self.scroll_text.bbox("all")[3]  # Get the height of the scroll region

        if scroll_region_height <= canvas_height:
            self.scrollbar.pack_forget()  # Hide the scrollbar
            self.scroll_text.unbind_all("<MouseWheel>")
            self.scroll_text.unbind_all("<Shift-MouseWheel>")
        else:
            self.scrollbar.pack(side=tk.RIGHT, fill="y")  # Show the scrollbar
            self.scroll_text.bind_all("<MouseWheel>", self._on_mousewheel)
            self.scroll_text.bind_all("<Shift-MouseWheel>", self._on_shiftmouse)
            self.scroll_text.bind_all("<Button-4>", self._on_mousewheel)  # For macOS compatibility
            self.scroll_text.bind_all("<Button-5>", self._on_mousewheel)  # For macOS compatibility
        
    def connect_bat(self):
        def on_entry_click(event):
            if text_space.get() == text_lang("Введите пароль", "Enter the password", language):
                text_space.delete(0, tk.END)
                text_space.configure(foreground="black")

        def on_focus_out(event):
            if text_space.get() == "":
                text_space.insert(0, text_lang("Введите пароль", "Enter the password", language))
                text_space.configure(foreground="gray")

        try:
            ports = list(serial.tools.list_ports.comports())
            for port in ports:
                if "CH340" in port.description:
                    self.port = port.device
            if self.port is None:
                raise SerialException
            self.ard = arduino(self.port, 115200)

            cmd_error, self.files_amount, self._block_status = self.ard.Init()

            # Clear previous widgets in box_text
            for widget in self.box_text.winfo_children():
                widget.destroy()

            if self._block_status:
                app_font = fonts[7]
                main_buttons_style = ttk.Style()
                main_buttons_style.configure("Unblock.TButton",          # имя стиля
                                    font=(app_font, 8),    # шрифт
                                    foreground="#000000",   # цвет текста
                                    # padding=10,             # отступы
                                    background=bg_color_grey)   # фоновый цвет
                grid = tk.Frame(self.box_text, pady=10, bg=bg_color_grey)
                self.is_connected_label.config(text=text_lang("Необходима разблокировка", "Unlocking is required", language))
                self.connect_button.config(state=tk.DISABLED)
                self.connect_button.config(state=tk.NORMAL, text=text_lang("Отключить весы", "Disconnect scales", language), command=self.disconnect_bat)
                grid.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
                text_space = ttk.Entry(grid, foreground="gray")
                text_space.insert(0, text_lang("Введите пароль", "Enter the password", language))

                text_space.bind("<FocusIn>", on_entry_click)
                text_space.bind("<FocusOut>", on_focus_out)
                text_space.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                unblock_btn = ttk.Button(grid, text=text_lang("Разблокировать", "Unlock", language), command=lambda: self.unblock_cmd(text_space.get()), style="Unblock.TButton")
                unblock_btn.pack(side=tk.LEFT, padx=5)
            else:
                self.is_connected_label.config(text=text_lang("Весы подключены", "Scales are connected", language), foreground="#004D40")
                # self.connect_button.config(state=tk.DISABLED)
                self.connect_button.config(state=tk.NORMAL, text=text_lang("Отключить весы", "Disconnect", language), command=self.disconnect_bat)
                self.date_time_button.config(state=tk.NORMAL)

                if self.files_amount != 0:
                    error_list, self.files = self.ard.File_Info(self.files_amount)
                    for widget in self.box_text.winfo_children():
                        widget.destroy()
                    for message in self.files:
                        label = SingleFile(self.box_text, message, self.ard, self)
                        label.pack(fill=tk.X, padx=5, pady=2, expand=True)
                else:
                    for widget in self.box_text.winfo_children():
                        widget.destroy()
                    text_space = ttk.Label(self.box_text, text=text_lang("Нет файлов", "No files", language), background=bg_color_light)
                    text_space.pack(pady=10)
        except SerialException:
            self.is_connected_label.config(text=text_lang("Весы не обнаружены", "Scales are not found", language))

    def disconnect_bat(self):
        self.ard.close_com_port()
        self.is_connected_label.config(text=text_lang("Весы отключены", "Scales are disconnected", language), foreground="#000000")
        self.connect_button.config(state=tk.NORMAL, text=text_lang("Подключить весы", "Connect to scales", language), command=self.connect_bat)
        self.date_time_button.config(state=tk.DISABLED)
        for widget in self.box_text.winfo_children():
            widget.destroy()

    def unblock_cmd(self, pwd):
        try:
            int(pwd)
        except ValueError:
            pwd = 0
        _, st = self.ard.Unblock_Scales(int(pwd))
        if st:
            self._block_status = True
            self.disconnect_bat()
            
            app_font = fonts[7]
            label_style = ttk.Style()
            label_style.configure("Unblosck.TLabel",          # имя стиля
                                font=(app_font, 10),    # шрифт
                                foreground="#000000",   # цвет текста
                                padding=10, background=bg_color_app)


            ttk.Label(self.box_text, text=text_lang("Весы успешно разблокированы", "Scales were unlocked successfully", language), style="Unblosck.TLabel").pack(pady=10)

    def set_time(self):
        print(self.ard.Set_Time())
        messagebox.showinfo("Time set", text_lang(f"Время успешно установлено", f"Time has been successfully set", language))

class SingleFile(tk.Frame):
    def __init__(self, master, data, arduino, main_window, **kwargs):
        super().__init__(master, relief=tk.RAISED, borderwidth=1, **kwargs, background=bg_color_dark)
        self.arduino = arduino
        self.data = data
        self.main_window = main_window
        self.create_widgets()

    def create_widgets(self):
        app_font = fonts[7]
        main_buttons_style = ttk.Style()
        main_buttons_style.configure("Main.TButton",          # имя стиля
                            font=(app_font, 8),    # шрифт
                            foreground="#000000",   # цвет текста
                            # padding=10,             # отступы
                            background=bg_color_dark)   # фоновый цвет
        
        label_style = ttk.Style()
        label_style.configure("Main.TLabel",          # имя стиля
                            font=(app_font, 8),    # шрифт
                            foreground="#000000",   # цвет текста
                            padding=10, background=bg_color_dark)
        
        save_btn_bat = ttk.Button(self, text=text_lang("Скачать BAT", "Save BAT", language), command=self.on_click_bat, style="Main.TButton", width=11)
        save_btn_bat.pack(side=tk.LEFT, padx=5, pady=5, expand=False)

        save_btn_csv = ttk.Button(self, text=text_lang("Скачать csv", "Save csv", language), command=self.on_click_csv, style="Main.TButton", width=11)
        save_btn_csv.pack(side=tk.LEFT, padx=5, pady=5, expand=False)

        delete_btn = ttk.Button(self, text=text_lang("Удалить", "Delete", language), command=self.delete_file, style="Main.TButton", width=11)
        delete_btn.pack(side=tk.LEFT, padx=5, pady=5, expand=False)

        file_label = ttk.Label(self, text=f"File: {self.data['name']}, Weightings: {self.data['lines'] - 2}, Time: {datetime.fromtimestamp(self.data['unix']).astimezone(TIMEZONE)}", style="Main.TLabel", width=50)
        file_label.pack(side=tk.LEFT, padx=10, pady=5, expand=False, anchor='center')

    def on_click_bat(self):
        messages, error_list = self.arduino.Get_File(self.data['file'], self.data['lines'])

        self.temp_arr = []
        for message in messages:
            self.temp_arr.append(message)

        directory = os.getcwd() + '/DataFiles/BAT/' + datetime.today().strftime('%Y-%m-%d')
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.save_bat(directory, '')

    def on_click_csv(self):
        messages, error_list = self.arduino.Get_File(self.data['file'], self.data['lines'])

        self.temp_arr = []
        for message in messages:
            self.temp_arr.append(message)

        self.df = pd.DataFrame(self.temp_arr, index=np.linspace(1, self.data['lines'] - 2, self.data['lines'] - 2))
        self.df = self.df.reset_index(drop=True)
        self.df["Weight"] = self.df["Weight"].apply(lambda x: x / 1000)
        self.df["SavedDateTime"] = self.df["SavedDateTime"].apply(lambda x: datetime.fromtimestamp(x).astimezone(TIMEZONE))
        self.df.drop(columns='ID', inplace=True)

        directory = os.getcwd() + '/DataFiles/csv/' + datetime.today().strftime('%Y-%m-%d')
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.save_csv(directory, '')

    def delete_file(self):
        self.arduino.Delete_File(self.data['file'])
        self.pack_forget()

    def save_csv(self, path, filename):
        if filename == '':
            filename = self.data['name']
        filepath = os.path.join(path, filename + ".csv")
        self.df.to_csv(filepath, sep=';')
        messagebox.showinfo("Save CSV", text_lang(f"CSV файл сохранен в {filepath}", f"CSV file saved to {filepath}", language))

    def save_bat(self, path, filename):
        if filename == '':
            filename = self.data['name']
        filepath = os.path.join(path, filename + ".bat")
        if not path.endswith(("\\", "/")):
            path += "\\"
        origin_path = create_blank_db(path)
        add_weightings_table(path)
        add_file_table(path, 0, filename)
        for data in self.temp_arr:
            add_samples_table(path, data['WeighingId'], data['Weight'] / 1000.0, data['Flag'], get_julian_datetime(datetime.fromtimestamp(data['SavedDateTime']).astimezone(TIMEZONE)))
        save_db_in_file(path, filename, origin_path)
        messagebox.showinfo("Save BAT", text_lang(f"BAT файл сохранен в {filepath}", f"BAT file saved to {filepath}", language))

def main():
    root = tk.Tk()
    root.title("Agrobit Saver")
    root.iconbitmap('Agrobit_logo.ico')
    root.geometry("720x480")
    root.minsize(720, 480)
    root.config(background=bg_color_app)

    app = MainScreen(master=root)
    app.mainloop()

def text_lang(text_ru, text_eng, lang):
    if lang == "ru":
        return text_ru
    else:
        return text_eng

if __name__ == "__main__":
    # if not pyuac.isUserAdmin():
    #     print("Re-launching as admin!")
    #     pyuac.runAsAdmin()
    # else:
    #     main()
    main()