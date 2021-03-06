import tkinter as tk
import tkinter.messagebox
import time
import _thread
import win32api

bg_zero = "#f0f0f0"
bg_one = "#c0c0c0"


class CalData:
    def __init__(self):
        self.x1 = 0
        self.opt = ""
        self.rlt = 0
        self.cal_str = ''

        self.opts = "+-*/&|"

    def is_opts_valid(self, opt):
        if len(opt) != 1:
            return False
        return opt in self.opts

    def update_opt(self, opt):
        if not self.is_opts_valid(opt):
            return
        self.opt = opt

    def update_x1(self, x1, opt):
        self.x1 = x1
        self.update_opt(opt)
        self.cal_str = hex(x1) + ' ' + opt + ' '

    def cal_rlt(self, x2):
        if self.opt == '+':
            self.rlt = self.x1 + x2
        elif self.opt == "-":
            self.rlt = self.x1 - x2
        elif self.opt == "*":
            self.rlt = self.x1 * x2
        elif self.opt == "/":
            self.rlt = self.x1 / x2
        elif self.opt == "&":
            self.rlt = self.x1 & x2
        elif self.opt == "|":
            self.rlt = self.x1 | x2

        self.cal_str = hex(self.x1) + ' ' + self.opt + ' ' + hex(x2) + ' = ' + hex(self.rlt)
        return self.rlt


class CoreData:
    def __init__(self):
        self.root_win = tk.Tk()
        self.root_win.resizable(0, 0)

        self.bits = [0 for i in range(0, 64)]
        self.dec = 0
        self.hex = '0x0'
        self.records = []
        self.records_forward = []
        self.wait_cmd_str = ""

        self.cal_data = CalData()
        self.cal_str = tk.StringVar(self.root_win, '')

        # button area
        self.button_list = [tk.Button(self.root_win, text="0") for x in range(0, 64)]
        button_index = 64
        for row in range(0, 2):
            count = 0
            for column in range(0, 39):
                count = count + 1
                if count == 5:
                    count = 0
                    tk.Label(self.root_win, text=' ', width=1) \
                        .grid(row=row * 2, column=column, sticky=tk.W)
                    tk.Label(self.root_win, text=' ', width=1) \
                        .grid(row=row * 2 + 1, column=column, sticky=tk.W)
                else:
                    button_index = button_index - 1
                    self.button_list[button_index] = tk.Button(self.root_win, text="0", width=1)
                    self.button_list[button_index].bind("<Button-1>", self.bits_callback)
                    self.button_list[button_index].grid(row=row * 2, column=column, sticky=tk.W)
                    tk.Label(self.root_win, text=button_index, width=1, font=("", 8)) \
                        .grid(row=row * 2 + 1, column=column, sticky=tk.W)

        # hex and dec area
        tk.Label(self.root_win, text='hex:', width=4).grid(row=4, column=0, columnspan=2, sticky=tk.E)
        self.hex_show = tk.StringVar(self.root_win, '0x0')
        self.entry_hex = tk.Entry(self.root_win, width=20, textvariable=self.hex_show)
        self.entry_hex.grid(row=4, column=2, columnspan=10, sticky=tk.W)

        cb = 9
        tk.Label(self.root_win, text='dec:', width=4).grid(row=4, column=cb, columnspan=2, sticky=tk.E)
        self.dec_show = tk.StringVar(self.root_win, '0')
        self.entry_dec = tk.Entry(self.root_win, width=22, textvariable=self.dec_show)
        self.entry_dec.grid(row=4, column=cb+2, columnspan=22, sticky=tk.W)

        # left and right shift
        cb = 19
        tk.Button(self.root_win, text='<', width=1, command=self.left_shift).grid(row=4, column=cb, columnspan=2,
                                                                                   sticky=tk.E)
        self.shift_val = tk.StringVar(self.root_win, '01')
        self.entry_shift_val = tk.Entry(self.root_win, width=2, textvariable=self.shift_val)
        self.entry_shift_val.grid(row=4, column=cb + 2, columnspan=2)
        tk.Button(self.root_win, text='>', width=1, command=self.right_shift).grid(row=4, column=cb + 4, columnspan=2,
                                                                                    sticky=tk.W)
        # bit flip
        cb = 25
        tk.Button(self.root_win, text='bit flip', width=8, command=self.bit_flip).grid(row=4, column=cb, columnspan=2)

        # help
        cb = 28
        tk.Button(self.root_win, text='help', width=4, command=self.help).grid(row=4, column=cb, columnspan=2)

        # keep top
        cb = 31
        self.top_v = tk.IntVar()
        self.top = tk.Checkbutton(self.root_win, width=4, text='top', variable=self.top_v)
        self.top.grid(row=4, column=cb, columnspan=4, sticky=tk.W)

        # calculation area
        tk.Label(self.root_win, textvariable=self.cal_str, width=117).grid(row=5, column=0, columnspan=39)

        self.root_win.bind("<Key>", self.key_respond)
        _thread.start_new_thread(self.bg_process, ("Thread-1", 2,))
        tk.mainloop()

    def show_all(self):
        self.hex_show.set(self.hex)
        self.dec_show.set(self.dec)
        for i in range(0, 64):
            b_text = str(self.bits[i])
            if self.bits[i]:
                self.button_list[i].configure(text=b_text, bg=bg_one)
            else:
                self.button_list[i].configure(text=b_text, bg=bg_zero)

    def refresh_all_no_records(self, dec):
        if dec > 18446744073709551615:
            dec = self.dec
        self.dec = dec
        dec_temp = self.dec
        for i in range(0, 64):
            self.bits[i] = dec_temp & 0x1
            dec_temp = dec_temp >> 1
        self.hex = hex(self.dec)
        self.show_all()

    def refresh_all(self, dec):
        self.refresh_all_no_records(dec)
        records_end = self.records[-1] if self.records else []
        if self.dec != records_end:
            self.records.append(self.dec)
        self.records_forward = []

    def bits_callback(self, event):
        if event.widget['text'] == '0':
            event.widget['text'] = '1'
            event.widget['bg'] = bg_one
        else:
            event.widget['text'] = '0'
            event.widget['bg'] = bg_zero

        dec_temp = 0
        for i in range(0, 64):
            self.bits[i] = int(self.button_list[i]['text'], 10)
            if self.bits[i] != 0:
                dec_temp = dec_temp + pow(2, i)
        self.refresh_all(dec_temp)

    def correct_all_input(self):
        if len(self.hex_show.get()) < 2 or self.hex_show.get()[0:2] != '0x':
            hex_s = self.hex_show.get()
            num_s = 0
            for i in range(len(hex_s) - 1, -1, -1):
                num_s = i
                if hex_s[i] in "0123456789ABCDEFabcdef":
                    continue
                else:
                    break
            if num_s == 0:
                num_s = -1
            hex_s = '0x' + hex_s[num_s + 1:len(hex_s)]
            self.refresh_all(int(hex_s, 16))
            win32api.keybd_event(35, 0, 0, 0)

    def find_input_entry_and_update(self):
        if self.dec_show.get() != '' and int(self.dec_show.get(), 10) != self.dec:
            self.refresh_all(int(self.dec_show.get(), 10))
        if self.hex_show.get() != '' and int(self.hex_show.get(), 16) != self.dec:
            self.refresh_all(int(self.hex_show.get(), 16))

    # shift operation
    def left_shift(self):
        shift = int(self.shift_val.get())
        dec = int(self.dec_show.get()) << shift
        self.refresh_all(dec)

    def right_shift(self):
        shift = int(self.shift_val.get())
        dec = int(self.dec_show.get()) >> shift
        self.refresh_all(dec)

    def bit_flip(self):
        self.refresh_all(18446744073709551615 - self.dec)

    '''  '''

    def bg_process(self, arg1, arg2):
        while 1:
            # keep the window always on the top
            if self.top_v.get():
                self.root_win.wm_attributes('-topmost', 1)
            else:
                self.root_win.wm_attributes('-topmost', 0)

            try:
                self.correct_all_input()
                self.find_input_entry_and_update()
            except ValueError:
                pass

            time.sleep(0.01)

    def del_invalid_in_input(self, c):
        valid_char = "0123456789abcdefABCDEF"
        if c in valid_char:
            return
        if c in self.dec_show.get():
            str_temp = self.dec_show.get()
            str_temp = str_temp.replace(c, '')
            self.dec_show.set(str_temp)
        elif c in self.hex_show.get():
            str_temp = self.hex_show.get()
            str_temp = str_temp.replace(c, '')
            self.hex_show.set(str_temp)
        elif c in self.shift_val.get():
            str_temp = self.shift_val.get()
            str_temp = str_temp.replace(c, '')
            self.shift_val.set(str_temp)

    def detect_cmd(self, c, target_str):
        if c == ',' or c == '，':
            self.wait_cmd_str = ','
        else:
            if len(self.wait_cmd_str) == 0:
                return False
            if self.wait_cmd_str[0] == ',':
                self.wait_cmd_str = self.wait_cmd_str + c
            if self.wait_cmd_str == target_str:
                self.wait_cmd_str = ''
                return True
            if len(self.wait_cmd_str) > 10:
                self.wait_cmd_str = ''
        return False

    def key_respond(self, event):
        self.del_invalid_in_input(event.char)

        if event.char == '@':
            self.entry_dec.focus_set()
            win32api.keybd_event(35, 0, 0, 0)
        if event.char == '!' or event.char == '！':
            self.entry_hex.focus_set()
            win32api.keybd_event(35, 0, 0, 0)
        if event.char == '#':
            self.entry_shift_val.focus_set()
            win32api.keybd_event(35, 0, 0, 0)

        if event.char == '=':
            dec = self.cal_data.cal_rlt(self.dec)
            self.refresh_all(dec)
            self.cal_str.set(self.cal_data.cal_str)
            win32api.keybd_event(35, 0, 0, 0)
        if self.cal_data.is_opts_valid(event.char):
            self.cal_data.update_x1(self.dec, event.char)
            self.cal_str.set(self.cal_data.cal_str)
            self.refresh_all_no_records(0)

        if event.char == 'h':
            self.left_shift()
        if event.char == 'l':
            self.right_shift()
        if event.char == 'j':
            dec = int(self.dec_show.get()) >> 32
            self.refresh_all(dec)
        if event.char == 'k':
            dec = int(self.dec_show.get()) << 32
            self.refresh_all(dec)

        if event.char == 'z' or event.char == 'Z':
            if len(self.records) == 0:
                return
            dec = self.records.pop()
            self.records_forward.append(dec)
            self.refresh_all_no_records(dec)
            win32api.keybd_event(35, 0, 0, 0)

        if event.char == 'x' or event.char == 'X':
            if len(self.records_forward) == 0:
                return
            dec = self.records_forward.pop()
            self.records.append(dec)
            self.refresh_all_no_records(dec)
            win32api.keybd_event(35, 0, 0, 0)

        if self.detect_cmd(event.char, ",t"):
            if self.top_v.get() == 0:
                self.top_v.set(1)
            else:
                self.top_v.set(0)

        if event.char == '?' or event.char == '？':
            self.help()

    @staticmethod
    def help():
        help_str = \
            '?\t\t: show this help window\n' + \
            'shift + 1\t\t: focus to hex entry\n' + \
            'shift + 2\t\t: focus to dec entry\n' + \
            'shift + 3\t\t: focus to shift val entry\n' + \
            'h \ l \ j \ k\t\t: left/right/up/down shift the val\n' + \
            '+ \ - \ * \ / \ & \ |\t: the operator\n' + \
            '=\t\t: do the calculation\n' + \
            'z \ x\t\t: restore \ de-restore\n' + \
            ',t\t\t: keep on the top'
        tk.messagebox.askokcancel(title='shortcuts', message=help_str)


CoreData()
