import json
from threading import Thread
from tkinter import *
from tkinter import ttk

import cv2
import numpy as np
import pyautogui as pag

################################################
import pytesseract
# Прочитать обязательно перед тем,как работать с распознаванием текста.
# https://medium.com/@winston.smith.spb/python-ocr-for-pdf-or-compare-textract-pytesseract-and-pyocr-acb19122f38c
################################################

################################################
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
custom_config = r'--oem 3 --psm 13'
################################################

# Присваивание шаблонов контрольных изображений.
btn = cv2.imread(r'templates\btn.jpg', cv2.IMREAD_UNCHANGED)
shirt = cv2.imread(r'templates\shirt.jpg', cv2.IMREAD_UNCHANGED)
push = cv2.imread(r'templates\push.jpg', cv2.IMREAD_UNCHANGED)

# Настройки Open CV Варианты настроек представлены ниже. По молчанию TM_CCOEFF_NORMED, threshold = 0.6.
# cv.TM_CCOEFF, cv.TM_CCOEFF_NORMED, cv.TM_CCORR, cv.TM_CCORR_NORMED, cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED
method = cv2.TM_CCOEFF_NORMED
threshold = 0.6


# Создание класса интерфейса программы.
class App:
    def __init__(self):
        self.app_running = True  # - переменная работы приложения.
        self.interface_mode = False  # - переменная переключателя режимов интерфейса.
        # По умолчанию, интерфейс в режиме настройки.
        self.control_mode = True  # - переменная переключателя режимов управления интерфейсом программы.

        # Переменные, которые отображают позиции игроков, наличие оппонентов за столом и их действия.
        self.dealer_position = 0
        self.dealer_position_checkup = 0  # - Контрольная переменная для отслеживания изменения позиций игроков.
        self.rb_select_checkup = '00'  # - Контрольная переменная для отслеживания изменения положения радиокнопки.
        self.seat1 = False
        self.seat2 = False
        self.seat3 = False
        self.seat1_push = False
        self.seat2_push = False
        self.seat3_push = False
        self.seat4_push = False
        self.got_push = False  # Переменная говорящая о наличии/отсутствии пуша за столом.

        # Выгружаем из БД словарь значений радиокнопок и соответствующих им параметров рамок.
        with open('cords_dict.json', 'r') as cords_input_file:
            self.cords_dict = json.load(cords_input_file)

        # Основные настройки главного окна интерфейса.
        self.console = Tk()  # Обязательный протокол начала цикла tkinter.
        self.screen_width = self.console.winfo_screenwidth()  # Считывание ширины экрана.
        self.screen_height = self.console.winfo_screenheight()  # Считывание высоты экрана.
        self.console.wm_attributes('-topmost', 1)  # Параметры задают нахождение окна интерфейса поверх остальных окон.
        self.console.geometry('382x582+976+0')  # Параметр задаёт размеры окна интерфейса в пикселях.
        self.console.resizable(False, False)  # Не даёт пользователю прав на изменение экрана ОИ.
        self.console.config(bd=0, padx=0, pady=0, bg='black', highlightthickness=1, highlightcolor='white')
        # Задаёт отступы, обрамления и цвет фона.
        self.console.iconbitmap(r'images\console_icon.ico')  # Отображает иконку программы на ОИ.
        self.console.title('PokerSPY')  # Отображает название программы на ОИ.
        self.console.protocol('WM_DELETE_WINDOW', self.closer)

        # Динамические переменные, участвующие в работе интерфейса.
        self.x_cords = IntVar()
        self.y_cords = IntVar()
        self.width = 25
        self.height = 25
        self.rb = StringVar()  # Переменная значений для радиокнопки.

        # Холст для отображения диапазонов рук.
        self.range_canvas = Canvas(self.console, bd=0, height=297, highlightthickness=1)
        self.range_canvas.pack()

        # Создаём сетку рук для отображения в интерфейсе.
        self.hands_grid = LabelFrame(self.range_canvas, bd=0, padx=0, pady=0,
                                     highlightthickness=0, highlightbackground='black')
        self.hands_grid.place(x=0, y=0)

        self.hands_grid.grid_columnconfigure(0, minsize=30)
        self.hands_grid.grid_columnconfigure(1, minsize=29)
        self.hands_grid.grid_columnconfigure(2, minsize=29)
        self.hands_grid.grid_columnconfigure(3, minsize=29)
        self.hands_grid.grid_columnconfigure(4, minsize=29)
        self.hands_grid.grid_columnconfigure(5, minsize=29)
        self.hands_grid.grid_columnconfigure(6, minsize=30)
        self.hands_grid.grid_columnconfigure(7, minsize=29)
        self.hands_grid.grid_columnconfigure(8, minsize=29)
        self.hands_grid.grid_columnconfigure(9, minsize=29)
        self.hands_grid.grid_columnconfigure(10, minsize=29)
        self.hands_grid.grid_columnconfigure(11, minsize=29)
        self.hands_grid.grid_columnconfigure(12, minsize=30)

        # Выводим в интерфейс пользователя весь диапазон рук,
        # который по умолчанию будет неактивен и отображаться серым цветом.

        self.hAA = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='AA', font=('', '9', 'bold'))  # flat, groove, raised, ridge, solid, or sunken
        self.hAKs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='AKs', font=('', '9', 'bold'))
        self.hAQs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='AQs', font=('', '9', 'bold'))
        self.hAJs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='AJs', font=('', '9', 'bold'))
        self.hATs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='ATs', font=('', '9', 'bold'))
        self.hA9s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A9s', font=('', '9', 'bold'))
        self.hA8s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A8s', font=('', '9', 'bold'))
        self.hA7s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A7s', font=('', '9', 'bold'))
        self.hA6s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A6s', font=('', '9', 'bold'))
        self.hA5s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A5s', font=('', '9', 'bold'))
        self.hA4s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A4s', font=('', '9', 'bold'))
        self.hA3s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A3s', font=('', '9', 'bold'))
        self.hA2s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A2s', font=('', '9', 'bold'))
        self.hAKo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='AKo', font=('', '9', 'bold'))
        self.hAQo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='AQo', font=('', '9', 'bold'))
        self.hAJo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='AJo', font=('', '9', 'bold'))
        self.hATo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='ATo', font=('', '9', 'bold'))
        self.hA9o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A9o', font=('', '9', 'bold'))
        self.hA8o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A8o', font=('', '9', 'bold'))
        self.hA7o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A7o', font=('', '9', 'bold'))
        self.hA6o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A6o', font=('', '9', 'bold'))
        self.hA5o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A5o', font=('', '9', 'bold'))
        self.hA4o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A4o', font=('', '9', 'bold'))
        self.hA3o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A3o', font=('', '9', 'bold'))
        self.hA2o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='A2o', font=('', '9', 'bold'))

        self.hKK = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='KK', font=('', '9', 'bold'))
        self.hKQs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='KQs', font=('', '9', 'bold'))
        self.hKJs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='KJs', font=('', '9', 'bold'))
        self.hKTs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='KTs', font=('', '9', 'bold'))
        self.hK9s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K9s', font=('', '9', 'bold'))
        self.hK8s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K8s', font=('', '9', 'bold'))
        self.hK7s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K7s', font=('', '9', 'bold'))
        self.hK6s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K6s', font=('', '9', 'bold'))
        self.hK5s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K5s', font=('', '9', 'bold'))
        self.hK4s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K4s', font=('', '9', 'bold'))
        self.hK3s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K3s', font=('', '9', 'bold'))
        self.hK2s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K2s', font=('', '9', 'bold'))
        self.hKQo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='KQo', font=('', '9', 'bold'))
        self.hKJo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='KJo', font=('', '9', 'bold'))
        self.hKTo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='KTo', font=('', '9', 'bold'))
        self.hK9o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K9o', font=('', '9', 'bold'))
        self.hK8o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K8o', font=('', '9', 'bold'))
        self.hK7o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K7o', font=('', '9', 'bold'))
        self.hK6o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K6o', font=('', '9', 'bold'))
        self.hK5o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K5o', font=('', '9', 'bold'))
        self.hK4o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K4o', font=('', '9', 'bold'))
        self.hK3o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K3o', font=('', '9', 'bold'))
        self.hK2o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='K2o', font=('', '9', 'bold'))

        self.hQQ = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='QQ', font=('', '9', 'bold'))
        self.hQJs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='QJs', font=('', '9', 'bold'))
        self.hQTs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='QTs', font=('', '9', 'bold'))
        self.hQ9s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q9s', font=('', '9', 'bold'))
        self.hQ8s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q8s', font=('', '9', 'bold'))
        self.hQ7s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q7s', font=('', '9', 'bold'))
        self.hQ6s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q6s', font=('', '9', 'bold'))
        self.hQ5s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q5s', font=('', '9', 'bold'))
        self.hQ4s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q4s', font=('', '9', 'bold'))
        self.hQ3s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q3s', font=('', '9', 'bold'))
        self.hQ2s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q2s', font=('', '9', 'bold'))
        self.hQJo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='QJo', font=('', '9', 'bold'))
        self.hQTo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='QTo', font=('', '9', 'bold'))
        self.hQ9o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q9o', font=('', '9', 'bold'))
        self.hQ8o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q8o', font=('', '9', 'bold'))
        self.hQ7o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q7o', font=('', '9', 'bold'))
        self.hQ6o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q6o', font=('', '9', 'bold'))
        self.hQ5o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q5o', font=('', '9', 'bold'))
        self.hQ4o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q4o', font=('', '9', 'bold'))
        self.hQ3o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q3o', font=('', '9', 'bold'))
        self.hQ2o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='Q2o', font=('', '9', 'bold'))

        self.hJJ = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='JJ', font=('', '9', 'bold'))
        self.hJTs = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='JTs', font=('', '9', 'bold'))
        self.hJ9s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J9s', font=('', '9', 'bold'))
        self.hJ8s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J8s', font=('', '9', 'bold'))
        self.hJ7s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J7s', font=('', '9', 'bold'))
        self.hJ6s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J6s', font=('', '9', 'bold'))
        self.hJ5s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J5s', font=('', '9', 'bold'))
        self.hJ4s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J4s', font=('', '9', 'bold'))
        self.hJ3s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J3s', font=('', '9', 'bold'))
        self.hJ2s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J2s', font=('', '9', 'bold'))
        self.hJTo = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='JTo', font=('', '9', 'bold'))
        self.hJ9o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J9o', font=('', '9', 'bold'))
        self.hJ8o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J8o', font=('', '9', 'bold'))
        self.hJ7o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J7o', font=('', '9', 'bold'))
        self.hJ6o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J6o', font=('', '9', 'bold'))
        self.hJ5o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J5o', font=('', '9', 'bold'))
        self.hJ4o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J4o', font=('', '9', 'bold'))
        self.hJ3o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J3o', font=('', '9', 'bold'))
        self.hJ2o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='J2o', font=('', '9', 'bold'))

        self.hTT = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                         relief='solid', text='TT', font=('', '9', 'bold'))
        self.hT9s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T9s', font=('', '9', 'bold'))
        self.hT8s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T8s', font=('', '9', 'bold'))
        self.hT7s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T7s', font=('', '9', 'bold'))
        self.hT6s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T6s', font=('', '9', 'bold'))
        self.hT5s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T5s', font=('', '9', 'bold'))
        self.hT4s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T4s', font=('', '9', 'bold'))
        self.hT3s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T3s', font=('', '9', 'bold'))
        self.hT2s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T2s', font=('', '9', 'bold'))
        self.hT9o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T9o', font=('', '9', 'bold'))
        self.hT8o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T8o', font=('', '9', 'bold'))
        self.hT7o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T7o', font=('', '9', 'bold'))
        self.hT6o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T6o', font=('', '9', 'bold'))
        self.hT5o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T5o', font=('', '9', 'bold'))
        self.hT4o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T4o', font=('', '9', 'bold'))
        self.hT3o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T3o', font=('', '9', 'bold'))
        self.hT2o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='T2o', font=('', '9', 'bold'))

        self.h99 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='99', font=('', '9', 'bold'))
        self.h98s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='98s', font=('', '9', 'bold'))
        self.h97s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='97s', font=('', '9', 'bold'))
        self.h96s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='96s', font=('', '9', 'bold'))
        self.h95s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='95s', font=('', '9', 'bold'))
        self.h94s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='94s', font=('', '9', 'bold'))
        self.h93s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='93s', font=('', '9', 'bold'))
        self.h92s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='92s', font=('', '9', 'bold'))
        self.h98o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='98o', font=('', '9', 'bold'))
        self.h97o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='97o', font=('', '9', 'bold'))
        self.h96o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='96o', font=('', '9', 'bold'))
        self.h95o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='95o', font=('', '9', 'bold'))
        self.h94o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='94o', font=('', '9', 'bold'))
        self.h93o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='93o', font=('', '9', 'bold'))
        self.h92o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='92o', font=('', '9', 'bold'))

        self.h88 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='88', font=('', '9', 'bold'))
        self.h87s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='87s', font=('', '9', 'bold'))
        self.h86s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='86s', font=('', '9', 'bold'))
        self.h85s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='85s', font=('', '9', 'bold'))
        self.h84s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='84s', font=('', '9', 'bold'))
        self.h83s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='83s', font=('', '9', 'bold'))
        self.h82s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='82s', font=('', '9', 'bold'))
        self.h87o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='87o', font=('', '9', 'bold'))
        self.h86o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='86o', font=('', '9', 'bold'))
        self.h85o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='85o', font=('', '9', 'bold'))
        self.h84o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='84o', font=('', '9', 'bold'))
        self.h83o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='83o', font=('', '9', 'bold'))
        self.h82o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='82o', font=('', '9', 'bold'))

        self.h77 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='77', font=('', '9', 'bold'))
        self.h76s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='76s', font=('', '9', 'bold'))
        self.h75s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='75s', font=('', '9', 'bold'))
        self.h74s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='74s', font=('', '9', 'bold'))
        self.h73s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='73s', font=('', '9', 'bold'))
        self.h72s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='72s', font=('', '9', 'bold'))
        self.h76o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='76o', font=('', '9', 'bold'))
        self.h75o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='75o', font=('', '9', 'bold'))
        self.h74o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='74o', font=('', '9', 'bold'))
        self.h73o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='73o', font=('', '9', 'bold'))
        self.h72o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='72o', font=('', '9', 'bold'))

        self.h66 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='66', font=('', '9', 'bold'))
        self.h65s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='65s', font=('', '9', 'bold'))
        self.h64s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='64s', font=('', '9', 'bold'))
        self.h63s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='63s', font=('', '9', 'bold'))
        self.h62s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='62s', font=('', '9', 'bold'))
        self.h65o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='65o', font=('', '9', 'bold'))
        self.h64o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='64o', font=('', '9', 'bold'))
        self.h63o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='63o', font=('', '9', 'bold'))
        self.h62o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='62o', font=('', '9', 'bold'))

        self.h55 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='55', font=('', '9', 'bold'))
        self.h54s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='54s', font=('', '9', 'bold'))
        self.h53s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='53s', font=('', '9', 'bold'))
        self.h52s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='52s', font=('', '9', 'bold'))
        self.h54o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='54o', font=('', '9', 'bold'))
        self.h53o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='53o', font=('', '9', 'bold'))
        self.h52o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='52o', font=('', '9', 'bold'))

        self.h44 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='44', font=('', '9', 'bold'))
        self.h43s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='43s', font=('', '9', 'bold'))
        self.h42s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='42s', font=('', '9', 'bold'))
        self.h43o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='43o', font=('', '9', 'bold'))
        self.h42o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='42o', font=('', '9', 'bold'))

        self.h33 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='33', font=('', '9', 'bold'))
        self.h32s = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='32s', font=('', '9', 'bold'))
        self.h32o = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0,
                          relief='solid', text='32o', font=('', '9', 'bold'))
        self.h22 = Label(self.hands_grid, width=3, height=1, bd=1, highlightthickness=3, padx=0, pady=0, relief='solid',
                         text='22', font=('', '9', 'bold'))

        # Размещаем все руки в сетку интерфейса пользователя.
        self.hAA.grid(row=0, column=0, stick='we')
        self.hAKs.grid(row=0, column=1)
        self.hAQs.grid(row=0, column=2)
        self.hAJs.grid(row=0, column=3)
        self.hATs.grid(row=0, column=4)
        self.hA9s.grid(row=0, column=5)
        self.hA8s.grid(row=0, column=6, stick='we')
        self.hA7s.grid(row=0, column=7)
        self.hA6s.grid(row=0, column=8)
        self.hA5s.grid(row=0, column=9)
        self.hA4s.grid(row=0, column=10)
        self.hA3s.grid(row=0, column=11)
        self.hA2s.grid(row=0, column=12, stick='we')

        self.hAKo.grid(row=1, column=0, stick='we')
        self.hKK.grid(row=1, column=1)
        self.hKQs.grid(row=1, column=2)
        self.hKJs.grid(row=1, column=3)
        self.hKTs.grid(row=1, column=4)
        self.hK9s.grid(row=1, column=5)
        self.hK8s.grid(row=1, column=6, stick='we')
        self.hK7s.grid(row=1, column=7)
        self.hK6s.grid(row=1, column=8)
        self.hK5s.grid(row=1, column=9)
        self.hK4s.grid(row=1, column=10)
        self.hK3s.grid(row=1, column=11)
        self.hK2s.grid(row=1, column=12, stick='we')

        self.hAQo.grid(row=2, column=0, stick='we')
        self.hKQo.grid(row=2, column=1)
        self.hQQ.grid(row=2, column=2)
        self.hQJs.grid(row=2, column=3)
        self.hQTs.grid(row=2, column=4)
        self.hQ9s.grid(row=2, column=5)
        self.hQ8s.grid(row=2, column=6, stick='we')
        self.hQ7s.grid(row=2, column=7)
        self.hQ6s.grid(row=2, column=8)
        self.hQ5s.grid(row=2, column=9)
        self.hQ4s.grid(row=2, column=10)
        self.hQ3s.grid(row=2, column=11)
        self.hQ2s.grid(row=2, column=12, stick='we')

        self.hAJo.grid(row=3, column=0, stick='we')
        self.hKJo.grid(row=3, column=1)
        self.hQJo.grid(row=3, column=2)
        self.hJJ.grid(row=3, column=3)
        self.hJTs.grid(row=3, column=4)
        self.hJ9s.grid(row=3, column=5)
        self.hJ8s.grid(row=3, column=6, stick='we')
        self.hJ7s.grid(row=3, column=7)
        self.hJ6s.grid(row=3, column=8)
        self.hJ5s.grid(row=3, column=9)
        self.hJ4s.grid(row=3, column=10)
        self.hJ3s.grid(row=3, column=11)
        self.hJ2s.grid(row=3, column=12, stick='we')

        self.hATo.grid(row=4, column=0, stick='we')
        self.hKTo.grid(row=4, column=1)
        self.hQTo.grid(row=4, column=2)
        self.hJTo.grid(row=4, column=3)
        self.hTT.grid(row=4, column=4)
        self.hT9s.grid(row=4, column=5)
        self.hT8s.grid(row=4, column=6, stick='we')
        self.hT7s.grid(row=4, column=7)
        self.hT6s.grid(row=4, column=8)
        self.hT5s.grid(row=4, column=9)
        self.hT4s.grid(row=4, column=10)
        self.hT3s.grid(row=4, column=11)
        self.hT2s.grid(row=4, column=12, stick='we')

        self.hA9o.grid(row=5, column=0, stick='we')
        self.hK9o.grid(row=5, column=1)
        self.hQ9o.grid(row=5, column=2)
        self.hJ9o.grid(row=5, column=3)
        self.hT9o.grid(row=5, column=4)
        self.h99.grid(row=5, column=5)
        self.h98s.grid(row=5, column=6, stick='we')
        self.h97s.grid(row=5, column=7)
        self.h96s.grid(row=5, column=8)
        self.h95s.grid(row=5, column=9)
        self.h94s.grid(row=5, column=10)
        self.h93s.grid(row=5, column=11)
        self.h92s.grid(row=5, column=12, stick='we')

        self.hA8o.grid(row=6, column=0, stick='we')
        self.hK8o.grid(row=6, column=1)
        self.hQ8o.grid(row=6, column=2)
        self.hJ8o.grid(row=6, column=3)
        self.hT8o.grid(row=6, column=4)
        self.h98o.grid(row=6, column=5)
        self.h88.grid(row=6, column=6, stick='we')
        self.h87s.grid(row=6, column=7)
        self.h86s.grid(row=6, column=8)
        self.h85s.grid(row=6, column=9)
        self.h84s.grid(row=6, column=10)
        self.h83s.grid(row=6, column=11)
        self.h82s.grid(row=6, column=12, stick='we')

        self.hA7o.grid(row=7, column=0, stick='we')
        self.hK7o.grid(row=7, column=1)
        self.hQ7o.grid(row=7, column=2)
        self.hJ7o.grid(row=7, column=3)
        self.hT7o.grid(row=7, column=4)
        self.h97o.grid(row=7, column=5)
        self.h87o.grid(row=7, column=6, stick='we')
        self.h77.grid(row=7, column=7)
        self.h76s.grid(row=7, column=8)
        self.h75s.grid(row=7, column=9)
        self.h74s.grid(row=7, column=10)
        self.h73s.grid(row=7, column=11)
        self.h72s.grid(row=7, column=12, stick='we')

        self.hA6o.grid(row=8, column=0, stick='we')
        self.hK6o.grid(row=8, column=1)
        self.hQ6o.grid(row=8, column=2)
        self.hJ6o.grid(row=8, column=3)
        self.hT6o.grid(row=8, column=4)
        self.h96o.grid(row=8, column=5)
        self.h86o.grid(row=8, column=6, stick='we')
        self.h76o.grid(row=8, column=7)
        self.h66.grid(row=8, column=8)
        self.h65s.grid(row=8, column=9)
        self.h64s.grid(row=8, column=10)
        self.h63s.grid(row=8, column=11)
        self.h62s.grid(row=8, column=12, stick='we')

        self.hA5o.grid(row=9, column=0, stick='we')
        self.hK5o.grid(row=9, column=1)
        self.hQ5o.grid(row=9, column=2)
        self.hJ5o.grid(row=9, column=3)
        self.hT5o.grid(row=9, column=4)
        self.h95o.grid(row=9, column=5)
        self.h85o.grid(row=9, column=6, stick='we')
        self.h75o.grid(row=9, column=7)
        self.h65o.grid(row=9, column=8)
        self.h55.grid(row=9, column=9)
        self.h54s.grid(row=9, column=10)
        self.h53s.grid(row=9, column=11)
        self.h52s.grid(row=9, column=12, stick='we')

        self.hA4o.grid(row=10, column=0, stick='we')
        self.hK4o.grid(row=10, column=1)
        self.hQ4o.grid(row=10, column=2)
        self.hJ4o.grid(row=10, column=3)
        self.hT4o.grid(row=10, column=4)
        self.h94o.grid(row=10, column=5)
        self.h84o.grid(row=10, column=6, stick='we')
        self.h74o.grid(row=10, column=7)
        self.h64o.grid(row=10, column=8)
        self.h54o.grid(row=10, column=9)
        self.h44.grid(row=10, column=10)
        self.h43s.grid(row=10, column=11)
        self.h42s.grid(row=10, column=12, stick='we')

        self.hA3o.grid(row=11, column=0, stick='we')
        self.hK3o.grid(row=11, column=1)
        self.hQ3o.grid(row=11, column=2)
        self.hJ3o.grid(row=11, column=3)
        self.hT3o.grid(row=11, column=4)
        self.h93o.grid(row=11, column=5)
        self.h83o.grid(row=11, column=6, stick='we')
        self.h73o.grid(row=11, column=7)
        self.h63o.grid(row=11, column=8)
        self.h53o.grid(row=11, column=9)
        self.h43o.grid(row=11, column=10)
        self.h33.grid(row=11, column=11)
        self.h32s.grid(row=11, column=12, stick='we')

        self.hA2o.grid(row=12, column=0, stick='we')
        self.hK2o.grid(row=12, column=1)
        self.hQ2o.grid(row=12, column=2)
        self.hJ2o.grid(row=12, column=3)
        self.hT2o.grid(row=12, column=4)
        self.h92o.grid(row=12, column=5)
        self.h82o.grid(row=12, column=6, stick='we')
        self.h72o.grid(row=12, column=7)
        self.h62o.grid(row=12, column=8)
        self.h52o.grid(row=12, column=9)
        self.h42o.grid(row=12, column=10)
        self.h32o.grid(row=12, column=11)
        self.h22.grid(row=12, column=12, stick='we')

        # Кортеж, в котором находятся сигналы ранков рук.
        # Нужен, чтобы обнулять значения бэкграунда сигналов в каждом раунде.
        self.hands_signals_tuple = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                    self.h66, self.h55, self.h44, self.h33, self.h22,
                                    self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                    self.hA6s, self.hA5s, self.hA4s, self.hA3s, self.hA2s,
                                    self.hKQs, self.hKJs, self.hKTs, self.hK9s, self.hK8s, self.hK7s, self.hK6s,
                                    self.hK5s, self.hK4s, self.hK3s, self.hK2s,
                                    self.hQJs, self.hQTs, self.hQ9s, self.hQ8s, self.hQ7s, self.hQ6s, self.hQ5s,
                                    self.hQ4s, self.hQ3s, self.hQ2s,
                                    self.hJTs, self.hJ9s, self.hJ8s, self.hJ7s, self.hJ6s, self.hJ5s, self.hJ4s,
                                    self.hJ3s, self.hJ2s,
                                    self.hT9s, self.hT8s, self.hT7s, self.hT6s, self.hT5s, self.hT4s, self.hT3s,
                                    self.hT2s,
                                    self.h98s, self.h97s, self.h96s, self.h95s, self.h94s, self.h93s, self.h92s,
                                    self.h87s, self.h86s, self.h85s, self.h84s, self.h83s, self.h82s,
                                    self.h76s, self.h75s, self.h74s, self.h73s, self.h72s,
                                    self.h65s, self.h64s, self.h63s, self.h62s,
                                    self.h54s, self.h53s, self.h52s, self.h43s, self.h42s, self.h32s,
                                    self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o, self.hA7o,
                                    self.hA6o, self.hA5o, self.hA4o, self.hA3o, self.hA2o,
                                    self.hKQo, self.hKJo, self.hKTo, self.hK9o, self.hK8o, self.hK7o, self.hK6o,
                                    self.hK5o, self.hK4o, self.hK3o, self.hK2o,
                                    self.hQJo, self.hQTo, self.hQ9o, self.hQ8o, self.hQ7o, self.hQ6o, self.hQ5o,
                                    self.hQ4o, self.hQ3o, self.hQ2o,
                                    self.hJTo, self.hJ9o, self.hJ8o, self.hJ7o, self.hJ6o, self.hJ5o, self.hJ4o,
                                    self.hJ3o, self.hJ2o,
                                    self.hT9o, self.hT8o, self.hT7o, self.hT6o, self.hT5o, self.hT4o, self.hT3o,
                                    self.hT2o,
                                    self.h98o, self.h97o, self.h96o, self.h95o, self.h94o, self.h93o, self.h92o,
                                    self.h87o, self.h86o, self.h85o, self.h84o, self.h83o, self.h82o,
                                    self.h76o, self.h75o, self.h74o, self.h73o, self.h72o,
                                    self.h65o, self.h64o, self.h63o, self.h62o,
                                    self.h54o, self.h53o, self.h52o, self.h43o, self.h42o, self.h32o)

        # Холст для отображения информации интерфейса.
        self.interface_canvas = Canvas(self.console, bd=0, bg='#8B4513', height=280, highlightthickness=0)
        self.interface_canvas.pack()

        # Кнопки для переключения режимов интерфейса.
        self.play_pic = PhotoImage(file=r'images\play_btn.png')
        self.setting_pic = PhotoImage(file=r'images\tuning_btn.png')
        self.manual_pic = PhotoImage(file=r'images\manual_btn.png')
        self.ai_pic = PhotoImage(file=r'images\ai_btn.png')
        self.mode_btn = Button(self.interface_canvas, image=self.play_pic, bg='#8B4513', activebackground='#8B4513',
                               bd=0, highlightthickness=0, command=self.interface_mode_switcher)
        self.mode_btn.place(x=27, y=26, anchor='center', width=38, height=38)
        self.control_btn = Button(self.interface_canvas, image=self.manual_pic, bd=2, highlightthickness=0,
                                  padx=0, pady=0, command=self.control_mode_switcher)
        # relief must be flat, groove, raised, ridge, solid, or sunken

        # Динамические надписи.
        self.heading_label = Label(self.interface_canvas, bd=0, bg='#8B4513', fg='white', font=('', 8, 'bold'),
                                   text='ИНТЕРФЕЙС В РЕЖИМЕ НАСТРОЙКИ')
        self.heading_label.place(x=373, y=45, anchor='e')
        # n, ne, e, se, s, sw, w, nw, or center

        self.interface_canvas.create_line(5, 53, 373, 53, fill='white')

        self.label_style = ttk.Style()
        self.label_style.configure('TLabel', background='#8B4513', foreground='white', font=('', 11, 'bold'))

        self.seat1_label = ttk.Label(self.interface_canvas, style='TLabel', text='seat #1')
        self.seat1_label.place(x=115, y=77, anchor='center')
        self.seat2_label = ttk.Label(self.interface_canvas, style='TLabel', text='seat #2')
        self.seat2_label.place(x=185, y=77, anchor='center')
        self.seat3_label = ttk.Label(self.interface_canvas, style='TLabel', text='seat #3')
        self.seat3_label.place(x=255, y=77, anchor='center')
        self.seat4_label = ttk.Label(self.interface_canvas, style='TLabel', text='hero')
        self.seat4_label.place(x=325, y=77, anchor='center')
        self.btn_label = ttk.Label(self.interface_canvas, style='TLabel', text='btn')
        self.btn_label.place(x=80, y=95, anchor='ne')
        self.shirt_label = ttk.Label(self.interface_canvas, style='TLabel', text='shirt')
        self.shirt_label.place(x=80, y=125, anchor='ne')
        self.push_label = ttk.Label(self.interface_canvas, style='TLabel', text='push')
        self.push_label.place(x=80, y=155, anchor='ne')
        self.empty_label1 = ttk.Label(self.interface_canvas, style='TLabel', text='vs sb')
        self.empty_label2 = ttk.Label(self.interface_canvas, style='TLabel', text='vs co+')
        self.empty_label3 = ttk.Label(self.interface_canvas, style='TLabel', text='vs btn+sb')

        # Радиокнопки.
        self.rb_style = ttk.Style()
        self.rb_style.configure('TRadiobutton', padding=0, background='#8B4513')

        self.rb1 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='1',
                                   command=self.rb_select)
        self.rb1.place(x=120, y=105, anchor='center')
        self.rb2 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='2',
                                   command=self.rb_select)
        self.rb2.place(x=190, y=105, anchor='center')
        self.rb3 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='3',
                                   command=self.rb_select)
        self.rb3.place(x=260, y=105, anchor='center')
        self.rb4 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='4',
                                   command=self.rb_select)
        self.rb4.place(x=330, y=105, anchor='center')
        self.rb5 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='5',
                                   command=self.rb_select)
        self.rb5.place(x=120, y=135, anchor='center')
        self.rb6 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='6',
                                   command=self.rb_select)
        self.rb6.place(x=190, y=135, anchor='center')
        self.rb7 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='7',
                                   command=self.rb_select)
        self.rb7.place(x=260, y=135, anchor='center')
        self.rb8 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='8',
                                   command=self.rb_select)
        self.rb9 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='9',
                                   command=self.rb_select)
        self.rb9.place(x=120, y=165, anchor='center')
        self.rb10 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='10',
                                    command=self.rb_select)
        self.rb10.place(x=190, y=165, anchor='center')
        self.rb11 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='11',
                                    command=self.rb_select)
        self.rb11.place(x=260, y=165, anchor='center')
        self.rb12 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='12',
                                    command=self.rb_select)
        self.rb13 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='13',
                                    command=self.rb_select)
        self.rb14 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='14',
                                    command=self.rb_select)
        self.rb15 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='15',
                                    command=self.rb_select)
        self.rb16 = ttk.Radiobutton(self.interface_canvas, style='TRadiobutton', variable=self.rb, value='16',
                                    command=self.rb_select)

        # Создаём дополнительное прозрачное окно интерфейса размером в экран монитора
        # для расположения на нём холстов с рамками визуального отображения областей захвата игровых зон.
        # Задаём его параметры.
        self.play_area_capture = Toplevel(self.console)
        self.play_area_capture.geometry(f'{self.screen_width}x{self.screen_height}+0+0')
        self.play_area_capture.wm_attributes('-topmost', 1)
        self.play_area_capture.wm_attributes('-transparentcolor', 'black')
        self.play_area_capture.configure(bg='black')
        self.play_area_capture.overrideredirect(True)

        # Располагаем на дополнительном окне прозрачные холсты с рамками захвата игровых областей.
        # Рамки имеют активные границы и меняются при манипуляциях на клавиатуре.
        self.frame1 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame1.place(x=self.cords_dict.get('1')[0], y=self.cords_dict.get('1')[1], anchor='nw')
        self.frame2 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame2.place(x=self.cords_dict.get('2')[0], y=self.cords_dict.get('2')[1], anchor='nw')
        self.frame3 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame3.place(x=self.cords_dict.get('3')[0], y=self.cords_dict.get('3')[1], anchor='nw')
        self.frame4 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame4.place(x=self.cords_dict.get('4')[0], y=self.cords_dict.get('4')[1], anchor='nw')
        self.frame5 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame5.place(x=self.cords_dict.get('5')[0], y=self.cords_dict.get('5')[1], anchor='nw')
        self.frame6 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame6.place(x=self.cords_dict.get('6')[0], y=self.cords_dict.get('6')[1], anchor='nw')
        self.frame7 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame7.place(x=self.cords_dict.get('7')[0], y=self.cords_dict.get('7')[1], anchor='nw')
        self.frame9 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                             highlightbackground='red', highlightthickness=1)
        self.frame9.place(x=self.cords_dict.get('9')[0], y=self.cords_dict.get('9')[1], anchor='nw')
        self.frame10 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                              highlightbackground='red', highlightthickness=1)
        self.frame10.place(x=self.cords_dict.get('10')[0], y=self.cords_dict.get('10')[1], anchor='nw')
        self.frame11 = Canvas(self.play_area_capture, width=self.width, height=self.height, bg='black',
                              highlightbackground='red', highlightthickness=1)
        self.frame11.place(x=self.cords_dict.get('11')[0], y=self.cords_dict.get('11')[1], anchor='nw')

        # Задаём управление границами рамок захвата с клавиатуры.
        self.interface_canvas.bind_all('<KeyPress>', self.left_top_corner_keypad)

        # Обязательный протокол завершения цикла tkinter.
        self.console.mainloop()

    # Метод, который отправляет параметры рамок захвата и значения радиокнопок в главный словарь координат рамок.
    def collector(self):
        self.cords_dict.update({self.rb.get(): [self.x_cords.get(), self.y_cords.get()]})

    # Метод, который задаёт координату по X для рамок захвата игрового поля.
    def x_cords_frame_set(self):
        if self.rb.get() == '1':
            self.frame1.place(x=self.cords_dict.get('1')[0])
        elif self.rb.get() == '2':
            self.frame2.place(x=self.cords_dict.get('2')[0])
        elif self.rb.get() == '3':
            self.frame3.place(x=self.cords_dict.get('3')[0])
        elif self.rb.get() == '4':
            self.frame4.place(x=self.cords_dict.get('4')[0])
        elif self.rb.get() == '5':
            self.frame5.place(x=self.cords_dict.get('5')[0])
        elif self.rb.get() == '6':
            self.frame6.place(x=self.cords_dict.get('6')[0])
        elif self.rb.get() == '7':
            self.frame7.place(x=self.cords_dict.get('7')[0])
        elif self.rb.get() == '9':
            self.frame9.place(x=self.cords_dict.get('9')[0])
        elif self.rb.get() == '10':
            self.frame10.place(x=self.cords_dict.get('10')[0])
        elif self.rb.get() == '11':
            self.frame11.place(x=self.cords_dict.get('11')[0])

    # Метод, который задаёт координаты по Y для рамок захвата игрового поля.
    def y_cords_frame_set(self):
        if self.rb.get() == '1':
            self.frame1.place(y=self.cords_dict.get('1')[1])
        elif self.rb.get() == '2':
            self.frame2.place(y=self.cords_dict.get('2')[1])
        elif self.rb.get() == '3':
            self.frame3.place(y=self.cords_dict.get('3')[1])
        elif self.rb.get() == '4':
            self.frame4.place(y=self.cords_dict.get('4')[1])
        elif self.rb.get() == '5':
            self.frame5.place(y=self.cords_dict.get('5')[1])
        elif self.rb.get() == '6':
            self.frame6.place(y=self.cords_dict.get('6')[1])
        elif self.rb.get() == '7':
            self.frame7.place(y=self.cords_dict.get('7')[1])
        elif self.rb.get() == '9':
            self.frame9.place(y=self.cords_dict.get('9')[1])
        elif self.rb.get() == '10':
            self.frame10.place(y=self.cords_dict.get('10')[1])
        elif self.rb.get() == '11':
            self.frame11.place(y=self.cords_dict.get('11')[1])

    # Метод, который задаёт координаты верхнего левого угла рамок захвата в режиме отладки
    # и записывает их в словарь координат self.cords_dict.
    # Управление осуществляется через клавиатуру.
    def left_top_corner_keypad(self, key):
        if not self.interface_mode:
            if key.keysym == 'Left':
                self.x_cords.set(self.x_cords.get() - 1)
                if self.x_cords.get() < 0:
                    self.x_cords.set(0)
                self.collector()
                self.x_cords_frame_set()

            if key.keysym == 'Right':
                self.x_cords.set(self.x_cords.get() + 1)
                if self.x_cords.get() + self.width > self.screen_width:
                    self.x_cords.set(self.screen_width - self.width)
                self.collector()
                self.x_cords_frame_set()

            if key.keysym == 'Up':
                self.y_cords.set(self.y_cords.get() - 1)
                if self.y_cords.get() < 0:
                    self.y_cords.set(0)
                self.collector()
                self.y_cords_frame_set()

            if key.keysym == 'Down':
                self.y_cords.set(self.y_cords.get() + 1)
                if self.y_cords.get() + self.height > self.screen_height:
                    self.y_cords.set(self.screen_height - self.height)
                self.collector()
                self.y_cords_frame_set()

    # Метод, который отвечает за переключение радиокнопок и выставляет границы рамок захвата игровой области
    # по параметрам из словаря координат self.cords_dict.
    def rb_select(self):
        if self.interface_mode:
            if self.rb_select_checkup != self.rb.get():
                pare_box = ()
                suited_box = ()
                offsuited_box = ()
                for bg in self.hands_signals_tuple:
                    bg['bg'] = 'SystemButtonFace'

                if self.rb.get() == '1':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44, self.h33, self.h22)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hA6s, self.hA5s, self.hA4s, self.hA3s, self.hA2s,
                                  self.hKQs, self.hKJs, self.hKTs,
                                  self.hQJs, self.hQTs, self.hQ9s,
                                  self.hJTs, self.hJ9s,
                                  self.hT9s)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o,
                                     self.hKQo, self.hKJo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '2':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44, self.h33, self.h22)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hA6s, self.hA5s, self.hA4s, self.hA3s, self.hA2s,
                                  self.hKQs, self.hKJs, self.hKTs, self.hK9s, self.hK8s,
                                  self.hQJs, self.hQTs, self.hQ9s,
                                  self.hJTs, self.hJ9s, self.hJ8s,
                                  self.hT9s, self.hT8s,
                                  self.h98s,
                                  self.h87s)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o, self.hA7o,
                                     self.hA6o, self.hA5o, self.hA4o, self.hA3o, self.hA2o,
                                     self.hKQo, self.hKJo, self.hKTo,
                                     self.hQJo,
                                     self.hJTo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '3':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44, self.h33, self.h22)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hA6s, self.hA5s, self.hA4s, self.hA3s, self.hA2s,
                                  self.hKQs, self.hKJs, self.hKTs, self.hK9s, self.hK8s, self.hK7s, self.hK6s,
                                  self.hK5s, self.hK4s, self.hK3s, self.hK2s,
                                  self.hQJs, self.hQTs, self.hQ9s, self.hQ8s, self.hQ7s, self.hQ6s, self.hQ5s,
                                  self.hQ4s, self.hQ3s,
                                  self.hJTs, self.hJ9s, self.hJ8s, self.hJ7s, self.hJ6s, self.hJ5s,
                                  self.hT9s, self.hT8s, self.hT7s, self.hT6s,
                                  self.h98s, self.h97s, self.h96s,
                                  self.h87s, self.h86s, self.h85s,
                                  self.h76s, self.h75s,
                                  self.h65s, self.h64s,
                                  self.h54s)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o, self.hA7o,
                                     self.hA6o, self.hA5o, self.hA4o, self.hA3o, self.hA2o,
                                     self.hKQo, self.hKJo, self.hKTo, self.hK9o, self.hK8o, self.hK7o, self.hK6o,
                                     self.hK5o, self.hK4o, self.hK3o, self.hK2o,
                                     self.hQJo, self.hQTo, self.hQ9o, self.hQ8o,
                                     self.hJTo, self.hJ9o,
                                     self.hT9o, self.hT8o,
                                     self.h98o)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '6':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s,
                                  self.hKQs, self.hKJs)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '7':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hKQs, self.hKJs)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o,
                                     self.hKQo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '8':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44, self.h33)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hA6s, self.hA5s, self.hA4s, self.hA3s,
                                  self.hKQs, self.hKJs, self.hKTs,
                                  self.hQJs)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o,
                                     self.hKQo, self.hKJo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '11':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44, self.h33)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hA6s, self.hA5s, self.hA4s,
                                  self.hKQs, self.hKJs, self.hKTs,
                                  self.hQJs)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o, self.hA7o,
                                     self.hKQo, self.hKJo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '12':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44, self.h33, self.h22)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hA6s, self.hA5s, self.hA4s, self.hA3s, self.hA2s,
                                  self.hKQs, self.hKJs, self.hKTs, self.hK9s,
                                  self.hQJs, self.hQTs)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o, self.hA7o,
                                     self.hA6o, self.hA5o,
                                     self.hKQo, self.hKJo, self.hKTo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '13':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44, self.h33, self.h22)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s, self.hA8s, self.hA7s,
                                  self.hA6s, self.hA5s, self.hA4s, self.hA3s, self.hA2s,
                                  self.hKQs, self.hKJs, self.hKTs, self.hK9s, self.hK8s, self.hK7s, self.hK6s,
                                  self.hK5s, self.hK4s, self.hK3s, self.hK2s,
                                  self.hQJs, self.hQTs, self.hQ9s, self.hQ8s, self.hQ7s,
                                  self.hJTs, self.hJ9s, self.hJ8s,
                                  self.hT9s)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo, self.hA9o, self.hA8o, self.hA7o,
                                     self.hA6o, self.hA5o, self.hA4o, self.hA3o, self.hA2o,
                                     self.hKQo, self.hKJo, self.hKTo, self.hK9o, self.hK8o, self.hK7o, self.hK6o,
                                     self.hQJo, self.hQTo, self.hQ9o,
                                     self.hJTo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '14':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs,
                                  self.hKQs)
                    offsuited_box = (self.hAKo, self.hAQo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '15':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs,
                                  self.hKQs, self.hKJs,
                                  self.hQJs)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo)
                    self.rb_select_checkup = self.rb.get()
                elif self.rb.get() == '16':
                    pare_box = (self.hAA, self.hKK, self.hQQ, self.hJJ, self.hTT, self.h99, self.h88, self.h77,
                                self.h66, self.h55, self.h44)
                    suited_box = (self.hAKs, self.hAQs, self.hAJs, self.hATs, self.hA9s,
                                  self.hKQs, self.hKJs, self.hKTs,
                                  self.hQJs, self.hQTs,
                                  self.hJTs)
                    offsuited_box = (self.hAKo, self.hAQo, self.hAJo, self.hATo,
                                     self.hKQo)
                    self.rb_select_checkup = self.rb.get()
                else:
                    for bg in self.hands_signals_tuple:
                        bg['bg'] = 'SystemButtonFace'

                for pare_card in pare_box:
                    pare_card['bg'] = 'SteelBlue'
                for suited_card in suited_box:
                    suited_card['bg'] = 'Gold'
                for offsuited_card in offsuited_box:
                    offsuited_card['bg'] = 'Tomato'
        else:
            self.x_cords.set(self.cords_dict.get(self.rb.get())[0])
            self.y_cords.set(self.cords_dict.get(self.rb.get())[1])

    def interface_mode_switcher(self):
        if self.interface_mode:
            self.interface_mode = False
            self.rb.set('0')
            for bg in self.hands_signals_tuple:
                bg['bg'] = 'SystemButtonFace'
            self.widget_destroyer()

            self.interface_canvas['bg'] = '#8B4513'
            self.mode_btn['activebackground'] = '#8B4513'
            self.mode_btn['bg'] = '#8B4513'
            self.mode_btn['image'] = self.play_pic
            self.heading_label['text'] = 'ИНТЕРФЕЙС В РЕЖИМЕ НАСТРОЙКИ'
            self.heading_label['bg'] = '#8B4513'
            self.heading_label.place(x=373, y=45, anchor='e')
            self.label_style.configure('TLabel', background='#8B4513', foreground='white', font=('', 11, 'bold'))
            self.seat1_label['text'] = 'seat #1'
            self.seat1_label.place(x=115, y=77, anchor='center')
            self.seat2_label['text'] = 'seat #2'
            self.seat2_label.place(x=185, y=77, anchor='center')
            self.seat3_label['text'] = 'seat #3'
            self.seat3_label.place(x=255, y=77, anchor='center')
            self.seat4_label['text'] = 'hero'
            self.seat4_label.place(x=325, y=77, anchor='center')
            self.btn_label['text'] = 'btn'
            self.btn_label.place(x=80, y=95, anchor='ne')
            self.shirt_label['text'] = 'shirt'
            self.shirt_label.place(x=80, y=125, anchor='ne')
            self.push_label['text'] = 'push'
            self.push_label.place(x=80, y=155, anchor='ne')
            self.rb_style.configure('TRadiobutton', padding=0, background='#8B4513')
            self.rb1.place(x=120, y=105, anchor='center')
            self.rb2.place(x=190, y=105, anchor='center')
            self.rb3.place(x=260, y=105, anchor='center')
            self.rb4.place(x=330, y=105, anchor='center')
            self.rb5.place(x=120, y=135, anchor='center')
            self.rb6.place(x=190, y=135, anchor='center')
            self.rb7.place(x=260, y=135, anchor='center')
            self.rb9.place(x=120, y=165, anchor='center')
            self.rb10.place(x=190, y=165, anchor='center')
            self.rb11.place(x=260, y=165, anchor='center')
            self.frame1['highlightthickness'] = 1
            self.frame2['highlightthickness'] = 1
            self.frame3['highlightthickness'] = 1
            self.frame4['highlightthickness'] = 1
            self.frame5['highlightthickness'] = 1
            self.frame6['highlightthickness'] = 1
            self.frame7['highlightthickness'] = 1
            self.frame9['highlightthickness'] = 1
            self.frame10['highlightthickness'] = 1
            self.frame11['highlightthickness'] = 1

        else:
            self.saver()
            self.interface_mode = True
            if not self.control_mode:
                self.control_mode_switcher()
            self.rb.set('0')
            for bg in self.hands_signals_tuple:
                bg['bg'] = 'SystemButtonFace'
            self.widget_destroyer()

            self.interface_canvas['bg'] = '#00b400'
            self.mode_btn['bg'] = '#00b400'
            self.mode_btn['activebackground'] = '#00b400'
            self.mode_btn['image'] = self.setting_pic
            self.control_btn['bg'] = '#00b400'
            self.control_btn['activebackground'] = '#00b400'
            self.control_btn.place(x=72, y=27, anchor='center', width=34, height=34)
            self.heading_label['bg'] = '#00b400'
            self.heading_label['text'] = 'ИНТЕРФЕЙС В АВТОМАТИЧЕСКОМ РЕЖИМЕ ИГРЫ'
            self.heading_label.place(x=373, y=45, anchor='e')
            self.label_style.configure('TLabel', background='#00b400', foreground='white', font=('', 11, 'bold'))
            self.seat1_label['text'] = 'CO'
            self.seat1_label.place(x=115, y=77, anchor='center')
            self.seat2_label['text'] = 'BTN'
            self.seat2_label.place(x=185, y=77, anchor='center')
            self.seat3_label['text'] = 'SB'
            self.seat3_label.place(x=255, y=77, anchor='center')
            self.seat4_label['text'] = 'BB'
            self.seat4_label.place(x=325, y=77, anchor='center')
            self.btn_label['text'] = 'open'
            self.btn_label.place(x=80, y=95, anchor='ne')
            self.shirt_label['text'] = 'vs co'
            self.shirt_label.place(x=80, y=125, anchor='ne')
            self.push_label['text'] = 'vs btn'
            self.push_label.place(x=80, y=155, anchor='ne')
            self.empty_label1.place(x=80, y=185, anchor='ne')
            self.empty_label2.place(x=80, y=215, anchor='ne')
            self.empty_label3.place(x=80, y=245, anchor='ne')
            self.rb_style.configure('TRadiobutton', padding=0, background='#00b400')
            self.rb1.place(x=120, y=105, anchor='center')
            self.rb2.place(x=190, y=105, anchor='center')
            self.rb3.place(x=260, y=105, anchor='center')
            self.rb6.place(x=190, y=135, anchor='center')
            self.rb7.place(x=260, y=135, anchor='center')
            self.rb8.place(x=330, y=135, anchor='center')
            self.rb11.place(x=260, y=165, anchor='center')
            self.rb12.place(x=330, y=165, anchor='center')
            self.rb13.place(x=330, y=195, anchor='center')
            self.rb14.place(x=260, y=225, anchor='center')
            self.rb15.place(x=330, y=225, anchor='center')
            self.rb16.place(x=330, y=255, anchor='center')
            self.frame1['highlightthickness'] = 0
            self.frame2['highlightthickness'] = 0
            self.frame3['highlightthickness'] = 0
            self.frame4['highlightthickness'] = 0
            self.frame5['highlightthickness'] = 0
            self.frame6['highlightthickness'] = 0
            self.frame7['highlightthickness'] = 0
            self.frame9['highlightthickness'] = 0
            self.frame10['highlightthickness'] = 0
            self.frame11['highlightthickness'] = 0

            # В отдельном потоке запускаем основной цикл Режима Игры, чтобы исключить залипание виджетов интерфейса.
            Thread(target=self.game_loop, daemon=True).start()

    # Метод, который переключает режимы управления диапазонами с автоматического на ручное и обратно.
    def control_mode_switcher(self):
        if self.control_mode:
            self.control_mode = False
            self.rb.set('0')
            for bg in self.hands_signals_tuple:
                bg['bg'] = 'SystemButtonFace'
            self.widget_destroyer()

            self.interface_canvas['bg'] = '#FF0000'
            self.mode_btn['bg'] = '#FF0000'
            self.mode_btn['activebackground'] = '#FF0000'
            self.control_btn['image'] = self.ai_pic
            self.control_btn['bg'] = '#FF0000'
            self.control_btn['activebackground'] = '#FF0000'
            self.control_btn.place(x=72, y=27, anchor='center', width=34, height=34)
            self.heading_label['bg'] = '#FF0000'
            self.heading_label['text'] = 'ИНТЕРФЕЙС В РУЧНОМ РЕЖИМЕ ИГРЫ'
            self.heading_label.place(x=373, y=45, anchor='e')
            self.label_style.configure('TLabel', background='#FF0000', foreground='white', font=('', 11, 'bold'))
            self.seat1_label.place(x=115, y=77, anchor='center')
            self.seat2_label.place(x=185, y=77, anchor='center')
            self.seat3_label.place(x=255, y=77, anchor='center')
            self.seat4_label.place(x=325, y=77, anchor='center')
            self.btn_label.place(x=80, y=95, anchor='ne')
            self.shirt_label.place(x=80, y=125, anchor='ne')
            self.push_label.place(x=80, y=155, anchor='ne')
            self.empty_label1.place(x=80, y=185, anchor='ne')
            self.empty_label2.place(x=80, y=215, anchor='ne')
            self.empty_label3.place(x=80, y=245, anchor='ne')
            self.rb_style.configure('TRadiobutton', padding=0, background='#FF0000')
            self.rb1.place(x=120, y=105, anchor='center')
            self.rb2.place(x=190, y=105, anchor='center')
            self.rb3.place(x=260, y=105, anchor='center')
            self.rb6.place(x=190, y=135, anchor='center')
            self.rb7.place(x=260, y=135, anchor='center')
            self.rb8.place(x=330, y=135, anchor='center')
            self.rb11.place(x=260, y=165, anchor='center')
            self.rb12.place(x=330, y=165, anchor='center')
            self.rb13.place(x=330, y=195, anchor='center')
            self.rb14.place(x=260, y=225, anchor='center')
            self.rb15.place(x=330, y=225, anchor='center')
            self.rb16.place(x=330, y=255, anchor='center')

        else:
            self.control_mode = True
            self.rb.set('0')
            for bg in self.hands_signals_tuple:
                bg['bg'] = 'SystemButtonFace'
            self.widget_destroyer()

            self.interface_canvas['bg'] = '#00b400'
            self.mode_btn['bg'] = '#00b400'
            self.mode_btn['activebackground'] = '#00b400'
            self.control_btn['image'] = self.manual_pic
            self.control_btn['bg'] = '#00b400'
            self.control_btn['activebackground'] = '#00b400'
            self.control_btn.place(x=72, y=27, anchor='center', width=34, height=34)
            self.heading_label['bg'] = '#00b400'
            self.heading_label['text'] = 'ИНТЕРФЕЙС В АВТОМАТИЧЕСКОМ РЕЖИМЕ ИГРЫ'
            self.heading_label.place(x=373, y=45, anchor='e')
            self.label_style.configure('TLabel', background='#00b400', foreground='white', font=('', 11, 'bold'))
            self.seat1_label.place(x=115, y=77, anchor='center')
            self.seat2_label.place(x=185, y=77, anchor='center')
            self.seat3_label.place(x=255, y=77, anchor='center')
            self.seat4_label.place(x=325, y=77, anchor='center')
            self.btn_label.place(x=80, y=95, anchor='ne')
            self.shirt_label.place(x=80, y=125, anchor='ne')
            self.push_label.place(x=80, y=155, anchor='ne')
            self.empty_label1.place(x=80, y=185, anchor='ne')
            self.empty_label2.place(x=80, y=215, anchor='ne')
            self.empty_label3.place(x=80, y=245, anchor='ne')
            self.rb_style.configure('TRadiobutton', padding=0, background='#00b400')
            self.rb1.place(x=120, y=105, anchor='center')
            self.rb2.place(x=190, y=105, anchor='center')
            self.rb3.place(x=260, y=105, anchor='center')
            self.rb6.place(x=190, y=135, anchor='center')
            self.rb7.place(x=260, y=135, anchor='center')
            self.rb8.place(x=330, y=135, anchor='center')
            self.rb11.place(x=260, y=165, anchor='center')
            self.rb12.place(x=330, y=165, anchor='center')
            self.rb13.place(x=330, y=195, anchor='center')
            self.rb14.place(x=260, y=225, anchor='center')
            self.rb15.place(x=330, y=225, anchor='center')
            self.rb16.place(x=330, y=255, anchor='center')

    # Метод, который убирает все виджеты из окна интерфейса.
    def widget_destroyer(self):
        self.control_btn.place_forget()
        self.heading_label.place_forget()
        self.seat1_label.place_forget()
        self.seat2_label.place_forget()
        self.seat3_label.place_forget()
        self.seat4_label.place_forget()
        self.btn_label.place_forget()
        self.shirt_label.place_forget()
        self.push_label.place_forget()
        self.empty_label1.place_forget()
        self.empty_label2.place_forget()
        self.empty_label3.place_forget()
        self.rb1.place_forget()
        self.rb2.place_forget()
        self.rb3.place_forget()
        self.rb4.place_forget()
        self.rb5.place_forget()
        self.rb6.place_forget()
        self.rb7.place_forget()
        self.rb8.place_forget()
        self.rb9.place_forget()
        self.rb10.place_forget()
        self.rb11.place_forget()
        self.rb12.place_forget()
        self.rb13.place_forget()
        self.rb14.place_forget()
        self.rb15.place_forget()
        self.rb16.place_forget()

    # Создаёт скриншоты для указанных рамок захвата через библиотеку PyAutoGUI.
    def sct_maker(self, frame_name):
        left = self.cords_dict.get(frame_name)[0]
        top = self.cords_dict.get(frame_name)[1]
        width = self.width
        height = self.height
        sct = pag.screenshot(region=(left, top, width, height))
        #####################################################
        text = pytesseract.image_to_string(sct, config=custom_config)
        print(text.strip())
        ####################################################
        sct = np.array(sct)
        sct = cv2.cvtColor(sct, cv2.COLOR_RGB2BGR)
        return sct

    # Сравнивает шаблоны изображений в указанном фрейме захвата экрана.
    def match_comparator(self, frame_name, template_name):
        sct = self.sct_maker(frame_name)
        result = cv2.matchTemplate(sct, template_name, method)
        locations = np.where(result >= threshold)
        locations = list(zip(*locations[::-1]))
        return locations

    # Метод, который ищет позицию баттона во время игры.
    def btn_scanner(self):
        if self.match_comparator('1', btn):
            self.dealer_position = 1
            return

        if self.match_comparator('2', btn):
            self.dealer_position = 2
            return

        if self.match_comparator('3', btn):
            self.dealer_position = 3
            return

        if self.match_comparator('4', btn):
            self.dealer_position = 4
            return

    # Метод обнуляет значения раунда.
    def round_eraser(self):
        if self.dealer_position_checkup != self.dealer_position:
            self.seat1 = False
            self.seat2 = False
            self.seat3 = False
            self.seat1_push = False
            self.seat2_push = False
            self.seat3_push = False
            self.got_push = False
            if not self.control_mode:
                self.control_mode_switcher()
            else:
                self.rb.set('0')
            for bg in self.hands_signals_tuple:
                bg['bg'] = 'SystemButtonFace'
            self.rb_select_checkup = '00'
            self.dealer_position_checkup = self.dealer_position

    # Метод, который проверяет наличие игроков на конкретных местах.
    def seats_scanner(self):
        if not self.got_push:
            if not self.seat1 and self.match_comparator('5', shirt):
                self.seat1 = True

            if not self.seat2 and self.match_comparator('6', shirt):
                self.seat2 = True

            if not self.seat3 and self.match_comparator('7', shirt):
                self.seat3 = True

    # Метод, который ищет активных игроков в раздаче.
    def push_scanner(self):
        if not self.seat1_push and self.match_comparator('9', push):
            self.seat1_push = True
            self.got_push = True

        if not self.seat2_push and self.match_comparator('10', push):
            self.seat2_push = True
            self.got_push = True

        if not self.seat3_push and self.match_comparator('11', push):
            self.seat3_push = True
            self.got_push = True

    # Метод для определения и отбора уникальной ситуации за столом.
    def situation_selector(self):
        if self.control_mode:
            if self.dealer_position == 1:
                if self.seat1:
                    if self.seat2:
                        if self.seat3:
                            self.rb.set('1')
                            self.rb_select()
                            return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            if self.seat1_push:
                                if self.seat2_push:
                                    self.rb.set('16')
                                    self.rb_select()
                                    return
                                else:
                                    self.rb.set('12')
                                    self.rb_select()
                                    return
                            else:
                                self.rb.set('13')
                                self.rb_select()
                                return
                    else:
                        if self.seat2_push:
                            self.control_mode_switcher()
                            return
                        if self.seat3:
                            if self.seat1_push:
                                if self.seat3_push:
                                    self.rb.set('16')
                                    self.rb_select()
                                    return
                                else:
                                    self.rb.set('12')
                                    self.rb_select()
                                    return
                            else:
                                self.rb.set('13')
                                self.rb_select()
                                return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            self.rb.set('13')
                            self.rb_select()
                            return
                else:
                    if self.seat1_push:
                        self.control_mode_switcher()
                        return
                    return

            if self.dealer_position == 2:
                if self.seat1:
                    if self.seat2:
                        if self.seat3:
                            if self.seat1_push:
                                if self.seat2_push:
                                    if self.seat3_push:
                                        self.control_mode_switcher()
                                        return
                                    else:
                                        self.rb.set('15')
                                        self.rb_select()
                                        return
                                else:
                                    if self.seat3_push:
                                        self.rb.set('15')
                                        self.rb_select()
                                        return
                                    else:
                                        self.rb.set('8')
                                        self.rb_select()
                                        return
                            else:
                                if self.seat2_push:
                                    if self.seat3_push:
                                        self.rb.set('16')
                                        self.rb_select()
                                        return
                                    else:
                                        self.rb.set('12')
                                        self.rb_select()
                                        return
                                else:
                                    self.rb.set('13')
                                    self.rb_select()
                                    return

                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            if self.seat2_push:
                                self.rb.set('11')
                                self.rb_select()
                                return
                            else:
                                self.rb.set('3')
                                self.rb_select()
                                return
                    else:
                        if self.seat2_push:
                            self.control_mode_switcher()
                            return
                        return
                else:
                    if self.seat1_push:
                        self.control_mode_switcher()
                        return
                    if self.seat2:
                        if self.seat3:
                            if self.seat2_push:
                                if self.seat3_push:
                                    self.rb.set('16')
                                    self.rb_select()
                                    return
                                else:
                                    self.rb.set('12')
                                    self.rb_select()
                                    return
                            else:
                                self.rb.set('13')
                                self.rb_select()
                                return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            self.rb.set('13')
                            self.rb_select()
                            return
                    else:
                        if self.seat2_push:
                            self.control_mode_switcher()
                            return
                        return
            if self.dealer_position == 3:
                if self.seat1:
                    if self.seat2:
                        if self.seat3:
                            if self.seat2_push:
                                if self.seat3_push:
                                    self.rb.set('14')
                                    self.rb_select()
                                    return
                                else:
                                    self.rb.set('7')
                                    self.rb_select()
                                    return
                            else:
                                if self.seat3_push:
                                    self.rb.set('11')
                                    self.rb_select()
                                    return
                                else:
                                    self.rb.set('3')
                                    self.rb_select()
                                    return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            return
                    else:
                        if self.seat2_push:
                            self.control_mode_switcher()
                            return
                        if self.seat3:
                            if self.seat3_push:
                                self.rb.set('11')
                                self.rb_select()
                                return
                            else:
                                self.rb.set('3')
                                self.rb_select()
                                return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            return
                else:
                    if self.seat1_push:
                        self.control_mode_switcher()
                        return
                    if self.seat2:
                        if self.seat3:
                            if self.seat3_push:
                                self.rb.set('11')
                                self.rb_select()
                                return
                            else:
                                self.rb.set('3')
                                self.rb_select()
                                return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            return
                    else:
                        if self.seat2_push:
                            self.control_mode_switcher()
                            return
                        if self.seat3:
                            self.rb.set('13')
                            self.rb_select()
                            return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            return
            if self.dealer_position == 4:
                if self.seat1:
                    if self.seat2:
                        if self.seat3:
                            if self.seat3_push:
                                self.rb.set('6')
                                self.rb_select()
                                return
                            else:
                                self.rb.set('2')
                                self.rb_select()
                                return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            self.rb.set('2')
                            self.rb_select()
                            return
                    else:
                        if self.seat2_push:
                            self.control_mode_switcher()
                            return
                        if self.seat3:
                            self.rb.set('2')
                            self.rb_select()
                            return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            self.rb.set('3')
                            self.rb_select()
                            return
                else:
                    if self.seat1_push:
                        self.control_mode_switcher()
                        return
                    if self.seat2:
                        if self.seat3:
                            self.rb.set('2')
                            self.rb_select()
                            return
                        else:
                            if self.seat3_push:
                                self.control_mode_switcher()
                                return
                            self.rb.set('3')
                            self.rb_select()
                            return
                    else:
                        if self.seat2_push:
                            self.control_mode_switcher()
                            return
                        if self.seat3:
                            self.rb.set('3')
                            self.rb_select()

    # Главный цикл программы, в котором происходит считывание сигналов игрового поля.
    def game_loop(self):
        while self.app_running:
            try:
                self.btn_scanner()
                self.round_eraser()
                self.seats_scanner()
                self.push_scanner()
                self.situation_selector()
            except OSError:  # Имя ошибки меняется в зависимости от метода захвата экрана.
                self.interface_mode_switcher()

            if not self.interface_mode:
                return
        self.console.destroy()

    # Метод, который закрывает программу.
    def closer(self):
        self.saver()
        if not self.interface_mode:
            self.console.destroy()
        else:
            self.app_running = False

    # Метод, который сохраняет координаты границ рамок захвата игровой области в БД.
    def saver(self):
        with open('cords_dict.json', 'w') as cords_file:
            json.dump(self.cords_dict, cords_file)


App()  # Вызываем класс интерфейса.
