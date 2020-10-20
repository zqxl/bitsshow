import tkinter as tk
import time
import _thread
import win32api
import win32con

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
        print(f"x1:{self.x1},x2:{x2},opt:{self.opt}")
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
    def __init__(self, root_win):
        self.bits = [0 for i in range(0, 64)]
        self.dec = 0
        self.hex = '0x0'
        self.cal_data = CalData()

        self.root_win = root_win
        self.cal_str = tk.StringVar(root, '')
        self.entry_dec = tk.Entry(root_win, width=20, textvariable=dec_show)
        self.entry_hex = tk.Entry(root_win, width=18, textvariable=hex_show)
        self.shift_val = tk.StringVar(root, '01')
        self.entry_shift_val = tk.Entry(root_win, width=2, textvariable=self.shift_val)
        self.top_v = tk.IntVar()
        self.top = tk.Checkbutton(root_win, width=4, text='top', variable=self.top_v, command=self.top_callback)

        self.wait_cmd_str = ""

    def top_callback(self):
        print(self.top_v.get())

    def refresh_by_dec(self):
        if self.dec > 18446744073709551615:
            self.dec = 18446744073709551615
        dec_temp = self.dec
        for i in range(0, 64):
            self.bits[i] = dec_temp & 0x1
            dec_temp = dec_temp >> 1
        self.hex = hex(self.dec)

    def refresh_by_hex(self):
        self.dec = int(self.hex, 16)
        self.refresh_by_dec()

    def refresh_by_bits(self):
        dec_temp = 0
        for i in range(0, 64):
            if self.bits[i] != 0:
                dec_temp = dec_temp + pow(2, i)
        self.dec = dec_temp
        self.refresh_by_dec()

    def print_self(self):
        print(f'dec: {self.dec}')
        print(f'hex: {self.hex}')
        print('bits:')
        print(self.bits)


def show_all():
    global g_data
    global hex_show
    global dec_show
    hex_show.set(g_data.hex)
    dec_show.set(g_data.dec)
    for i in range(0, 64):
        b_text = str(g_data.bits[i])
        if g_data.bits[i]:
            button_list[i].configure(text=b_text, bg=bg_one)
        else:
            button_list[i].configure(text=b_text, bg=bg_zero)


def refresh_bits(event):
    global g_data
    print(event.widget['text'])
    if event.widget['text'] == '0':
        event.widget['text'] = '1'
        event.widget['bg'] = bg_one
    else:
        event.widget['text'] = '0'
        event.widget['bg'] = bg_zero

    for i in range(0, 64):
        g_data.bits[i] = int(button_list[i]['text'], 10)
    g_data.refresh_by_bits()
    show_all()


def refresh_hex_button():
    global g_data, hex_show
    refresh_hex(hex_show.get(), 0, 0)


def refresh_dec_button():
    global g_data, dec_show
    refresh_dec(dec_show.get(), 0, 0)


def refresh_hex(content, reason, name):
    global g_data, hex_show
    g_data.dec = int(content, 16)
    g_data.refresh_by_dec()
    show_all()
    return True


def refresh_dec(content, reason, name):
    global g_data, dec_show
    g_data.dec = int(content, 10)
    g_data.refresh_by_dec()
    show_all()
    return True


def left_shift():
    global dec_show, g_data
    shift = int(g_data.shift_val.get())
    g_data.dec = int(dec_show.get()) << shift
    g_data.refresh_by_dec()
    show_all()


def right_shift():
    global dec_show, g_data
    shift = int(g_data.shift_val.get())
    g_data.dec = int(dec_show.get()) >> shift
    g_data.refresh_by_dec()
    show_all()


def del_invalid_in_input(c):
    global g_data
    if c in dec_show.get():
        str_temp = dec_show.get()
        str_temp = str_temp.replace(c, '')
        dec_show.set(str_temp)
        refresh_dec_button()
    elif c in hex_show.get():
        str_temp = hex_show.get()
        str_temp = str_temp.replace(c, '')
        hex_show.set(str_temp)
        refresh_hex_button()
    elif c in g_data.shift_val.get():
        str_temp = g_data.shift_val.get()
        str_temp = str_temp.replace(c, '')
        g_data.shift_val.set(str_temp)


def detect_cmd(c, target_str):
    global g_data
    if c == ',' or c == '，':
        g_data.wait_cmd_str = ','
    else:
        if len(g_data.wait_cmd_str) == 0:
            return False
        if g_data.wait_cmd_str[0] == ',':
            g_data.wait_cmd_str = g_data.wait_cmd_str + c
        if g_data.wait_cmd_str == target_str:
            g_data.wait_cmd_str = ''
            return True
        if len(g_data.wait_cmd_str) > 10:
            g_data.wait_cmd_str = ''
    return False


def find_input_entry_and_update():
    global g_data, dec_show, hex_show
    if int(dec_show.get(), 10) != g_data.dec:
        refresh_dec(dec_show.get(), 0, 0)
    if int(hex_show.get(), 16) != g_data.dec:
        refresh_hex(hex_show.get(), 0, 0)


def root_call_back(event):
    global g_data, button_list, dec_show, hex_show

    valid_char = "0123456789abcdefABCDEFxX"
    if event.char in valid_char or event.char == '\b':
        find_input_entry_and_update()
    else:
        del_invalid_in_input(event.char)

    if event.char in valid_char or event.char == '\b':
        find_input_entry_and_update()
    else:
        del_invalid_in_input(event.char)

    if event.char == '@':
        g_data.entry_dec.focus_set()
        win32api.keybd_event(35, 0, 0, 0)
    if event.char == '!' or event.char == '！':
        g_data.entry_hex.focus_set()
        win32api.keybd_event(35, 0, 0, 0)
    if event.char == '#':
        g_data.entry_shift_val.focus_set()
        win32api.keybd_event(35, 0, 0, 0)
    if event.char == '=':
        button_list[0].focus_set()
        g_data.dec = g_data.cal_data.cal_rlt(g_data.dec)
        g_data.refresh_by_dec()
        show_all()
        g_data.cal_str.set(g_data.cal_data.cal_str)
    if g_data.cal_data.is_opts_valid(event.char):
        g_data.cal_data.update_x1(g_data.dec, event.char)
        g_data.cal_str.set(g_data.cal_data.cal_str)
    if event.char == 'h':
        left_shift()
    if event.char == 'l':
        right_shift()
    if event.char == 'j':
        g_data.dec = int(dec_show.get()) >> 32
        g_data.refresh_by_dec()
        show_all()
    if event.char == 'k':
        g_data.dec = int(dec_show.get()) << 32
        g_data.refresh_by_dec()
        show_all()

    if detect_cmd(event.char, ",t"):
        if g_data.top_v.get() == 0:
            g_data.top_v.set(1)
        else:
            g_data.top_v.set(0)


def correct_all_input():
    global hex_show
    if hex_show.get()[0:2] != '0x':
        hex_show.set("0x")
        win32api.keybd_event(35, 0, 0, 0)


def keep_win_top(arg1, arg2):
    global g_data
    while 1:
        if g_data.top_v.get():
            g_data.root_win.wm_attributes('-topmost', 1)
        else:
            g_data.root_win.wm_attributes('-topmost', 0)
        try:
            find_input_entry_and_update()
            correct_all_input()
        except ValueError:
            pass

        time.sleep(0.1)


def main(root_win):
    global g_data, hex_show, dec_show, button_list, shift_val
    button_width = 1

    root_win.title('bitsshow')
    _thread.start_new_thread(keep_win_top, ("Thread-1", 2,))

    # buttons area
    button_index = 64
    for row in range(0, 2):
        count = 0
        for column in range(0, 39):
            count = count + 1
            if count == 5:
                count = 0
                tk.Label(root_win, text=' ', width=button_width) \
                    .grid(row=row * 2, column=column, sticky=tk.W)
                tk.Label(root_win, text=' ', width=button_width) \
                    .grid(row=row * 2 + 1, column=column, sticky=tk.W)
            else:
                button_index = button_index - 1
                button_list[button_index] = tk.Button(root_win, text="0", width=button_width)
                button_list[button_index].bind("<Button-1>", refresh_bits)
                button_list[button_index].grid(row=row * 2, column=column, sticky=tk.W)
                tk.Label(root_win, text=button_index, width=button_width, font=("", 8)) \
                    .grid(row=row * 2 + 1, column=column, sticky=tk.W)

    ''' hex and dec '''
    tk.Label(root_win, text='hex:', width=button_width * 4).grid(row=4, column=0, columnspan=2, sticky=tk.E)
    g_data.entry_hex.grid(row=4, column=2, columnspan=8, sticky=tk.W)

    tk.Label(root_win, text='dec:', width=button_width * 4).grid(row=4, column=8, columnspan=2, sticky=tk.E)
    g_data.entry_dec.grid(row=4, column=10, columnspan=10, sticky=tk.W)

    ''' left and right shift '''
    tk.Button(root_win, text='<<', width=2, command=left_shift).grid(row=4, column=25, columnspan=2, sticky=tk.E)
    g_data.entry_shift_val.grid(row=4, column=27, columnspan=2)
    tk.Button(root_win, text='>>', width=2, command=right_shift).grid(row=4, column=29, columnspan=2, sticky=tk.W)
    g_data.top.grid(row=4, column=31, columnspan=4, sticky=tk.W)

    ''' 运算区 '''
    root.bind("<Key>", root_call_back)
    tk.Label(root_win, textvariable=g_data.cal_str, width=117) \
        .grid(row=5, column=0, columnspan=39)

    tk.mainloop()


if __name__ == '__main__':
    '''
    data = CoreData()
    data.dec = 23
    data.refresh_by_dec()
    data.print_self()
    data.refresh_by_hex()
    data.print_self()
    data.refresh_by_bits()
    data.print_self()
    '''
    root = tk.Tk()
    root.resizable(0, 0)
    hex_show = tk.StringVar(root, '0x0')
    dec_show = tk.StringVar(root, '0')
    button_list = [tk.Button(root) for x in range(0, 64)]

    g_data = CoreData(root)

    main(root)
