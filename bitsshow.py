import tkinter as tk
import tkinter.messagebox
import time
import _thread
import win32api

# from pynput.keyboard import Listener
import pynput

bg_zero = "#f0f0f0"
bg_one = "#c0c0c0"
bg_to_pressed = "#c0c0c0"


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
            # self.rlt = int(self.x1 / x2)
            self.rlt = self.x1 / x2
        elif self.opt == "&":
            self.rlt = self.x1 & x2
        elif self.opt == "|":
            self.rlt = self.x1 | x2

        self.rlt = int(self.rlt)

        self.cal_str = hex(self.x1) + ' ' + self.opt + ' ' + hex(x2) + ' = ' + hex(self.rlt)
        return self.rlt


def get_bits_val(val, bit_start, bit_end):
    mask = (1 << (bit_end - bit_start + 1)) - 1
    return (val >> bit_start) & mask

def set_bits_val(val, bit_start, bit_end, bit_val):
    mask = (1 << (bit_end - bit_start + 1)) - 1
    bit_val = bit_val & mask
    val = val & (~(mask << bit_start))
    val = val | (bit_val << bit_start)
    return val

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
        self.cal_str = tk.StringVar(self.root_win, '0+0=0')

        # [[end, start], [end, start], ...]
        self.bits_extract_pos = []
        # [num1,         num2,         ...]
        self.bits_extract_rst = []

        self.bits_extract_hdl_entry_bits_start = []
        self.bits_extract_hdl_entry_bits_end = []
        self.bits_extract_hdl_entry_rst_hex = []
        self.bits_extract_hdl_entry_rst_dec = []
        self.bits_extract_hdl_btn_set_val = []
        self.bits_extract_hdl_btn_destroy = []

        self.bits_extract_hdl_lab_from = []
        self.bits_extract_hdl_lab_to = []
        self.bits_extract_hdl_lab_hex = []
        self.bits_extract_hdl_lab_dec = []

        # ########################################### bit button area ############################################
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

        # ########################################### hex and dec area ############################################
        g_row = 4
        tk.Label(self.root_win, text='hex:', width=4).grid(row=g_row, column=0, columnspan=2, sticky=tk.E)
        self.hex_show = tk.StringVar(self.root_win, '0x0')
        self.entry_hex = tk.Entry(self.root_win, width=20, textvariable=self.hex_show)
        self.entry_hex.grid(row=g_row, column=2, columnspan=10, sticky=tk.W)

        cb = 9
        tk.Label(self.root_win, text='dec:', width=4).grid(row=g_row, column=cb, columnspan=2, sticky=tk.E)
        self.dec_show = tk.StringVar(self.root_win, '0')
        self.entry_dec = tk.Entry(self.root_win, width=22, textvariable=self.dec_show)
        self.entry_dec.grid(row=g_row, column=cb + 2, columnspan=22, sticky=tk.W)

        # left and right shift
        cb = 19
        tk.Button(self.root_win, text='<', width=1, command=self.left_shift).grid(row=g_row, column=cb, columnspan=2,
                                                                                  sticky=tk.E)
        self.shift_val = tk.StringVar(self.root_win, '01')
        self.entry_shift_val = tk.Entry(self.root_win, width=2, textvariable=self.shift_val)
        self.entry_shift_val.grid(row=g_row, column=cb + 2, columnspan=2)
        tk.Button(self.root_win, text='>', width=1, command=self.right_shift).grid(row=g_row, column=cb + 4,
                                                                                   columnspan=2, sticky=tk.W)
        # bit flip
        cb = 25
        tk.Button(self.root_win, text='bit flip', width=8, command=self.bit_flip).grid(row=g_row, column=cb,
                                                                                       columnspan=2)

        # add bits grp
        cb = 26
        tk.Button(self.root_win, text='add bits grp', width=12, command=self.bit_extract_group_add).grid(row=g_row,
                                                                                                         column=cb,
                                                                                                         columnspan=8)

        # keep top
        cb = 33
        self.top_v = tk.IntVar()
        self.top = tk.Checkbutton(self.root_win, width=4, text='top', variable=self.top_v)
        self.top.grid(row=g_row, column=cb, columnspan=4, sticky=tk.W)

        # help
        cb = 35
        tk.Button(self.root_win, text='help', width=4, command=self.help).grid(row=g_row, column=cb, columnspan=4)

        # ########################################### calculation area ############################################
        g_row = g_row + 1
        t = tk.LabelFrame(self.root_win, text='calc', labelanchor='w')
        t.grid(row=g_row, column=0, columnspan=40, pady=5)

        tk.Label(t, textvariable=self.cal_str, width=100).grid(row=g_row, column=0)

        self.root_win.bind("<Key>", self.key_respond)
        _thread.start_new_thread(self.bg_process, ("Thread-1", 2,))


        # ########################################### bits extract area ############################################
        g_row = g_row + 1

        self.frame_bits_extract = tk.LabelFrame(self.root_win, text='bits', labelanchor='w')
        self.frame_bits_extract.grid(row=g_row, column=0, columnspan=96, sticky=tk.W)

        self.bit_extract_group_add()

        # ########################################### MAIN LOOP ############################################
        tk.mainloop()

    def bits_extract_update(self, *args):
        self.show_all()

    def bit_extract_group_add(self):
        """
                self.bits_extract_hdl_entry_bits_start = []
                self.bits_extract_hdl_entry_bits_end = []
                self.bits_extract_hdl_entry_rst_hex = []
                self.bits_extract_hdl_entry_rst_dec = []
        """
        row = len(self.bits_extract_hdl_entry_bits_start)

        # save vars
        self.bits_extract_pos.append(
            [tk.StringVar(self.frame_bits_extract, str(4 * row)), tk.StringVar(self.root_win, str(4 * row + 3))])
        self.bits_extract_pos[-1][0].trace("w", lambda name, index, mode, var=self: self.bits_extract_update(self))
        self.bits_extract_rst.append(
            [tk.StringVar(self.frame_bits_extract, '0'), tk.StringVar(self.root_win, '0')])

        BITS_EXTRACE_RST_WIDTH = 10
        # save component handles
        self.bits_extract_hdl_entry_bits_start.append(
            tk.Entry(self.frame_bits_extract, width=2, textvariable=self.bits_extract_pos[-1][0]))
        self.bits_extract_hdl_entry_bits_end.append(
            tk.Entry(self.frame_bits_extract, width=2, textvariable=self.bits_extract_pos[-1][1]))

        self.bits_extract_hdl_entry_rst_hex.append(
            tk.Entry(self.frame_bits_extract, width=BITS_EXTRACE_RST_WIDTH, textvariable=self.bits_extract_rst[-1][0]))
        self.bits_extract_hdl_entry_rst_dec.append(
            tk.Entry(self.frame_bits_extract, width=BITS_EXTRACE_RST_WIDTH, textvariable=self.bits_extract_rst[-1][1]))

        self.bits_extract_hdl_btn_set_val.append(
            tk.Button(self.frame_bits_extract, text='set val', width=6))
        self.bits_extract_hdl_btn_set_val[-1].bind("<Button-1>", self.bits_extract_btn_cb_set_val)

        self.bits_extract_hdl_btn_destroy.append(
            tk.Button(self.frame_bits_extract, text='X', width=1))
        self.bits_extract_hdl_btn_destroy[-1].bind("<Button-1>", self.bit_extract_group_del)
        row = row + 1
        cb = 0

        self.bits_extract_hdl_lab_from.append(tk.Label(self.frame_bits_extract, text='from:', width=4))
        self.bits_extract_hdl_lab_from[-1].grid(row=row, column=cb, sticky=tk.E)
        cb = cb + 4
        self.bits_extract_hdl_entry_bits_start[-1].grid(row=row, column=cb, columnspan=2)
        cb = cb + 2

        self.bits_extract_hdl_lab_to.append(tk.Label(self.frame_bits_extract, text='to:', width=2))
        self.bits_extract_hdl_lab_to[-1].grid(row=row, column=cb, sticky=tk.E)
        cb = cb + 2
        self.bits_extract_hdl_entry_bits_end[-1].grid(row=row, column=cb, columnspan=2)
        cb = cb + 16

        self.bits_extract_hdl_lab_hex.append(tk.Label(self.frame_bits_extract, text='val hex:', width=8))
        self.bits_extract_hdl_lab_hex[-1].grid(row=row, column=cb, sticky=tk.W)
        cb = cb + 8
        self.bits_extract_hdl_entry_rst_hex[-1].grid(row=row, column=cb, columnspan=BITS_EXTRACE_RST_WIDTH)
        cb = cb + BITS_EXTRACE_RST_WIDTH

        self.bits_extract_hdl_lab_dec.append(tk.Label(self.frame_bits_extract, text='val dec:', width=8))
        self.bits_extract_hdl_lab_dec[-1].grid(row=row, column=cb, sticky=tk.E)
        cb = cb + 8
        self.bits_extract_hdl_entry_rst_dec[-1].grid(row=row, column=cb, columnspan=BITS_EXTRACE_RST_WIDTH)
        cb = cb + BITS_EXTRACE_RST_WIDTH

        self.bits_extract_hdl_btn_set_val[-1].grid(row=row, column=cb, columnspan=6, sticky=tk.W, padx=6)
        cb = cb + 6

        self.bits_extract_hdl_btn_destroy[-1].grid(row=row, column=cb, columnspan=1, sticky=tk.W, padx=3)
        cb = cb + 1

        self.show_all()

    def bit_extract_group_del(self, event):
        event.widget['bg'] = bg_to_pressed

        for i in range(0, len(self.bits_extract_pos)):
            if self.bits_extract_hdl_btn_destroy[i]['bg'] == bg_to_pressed:
                print(i)
                self.bits_extract_pos.pop(i)
                self.bits_extract_rst.pop(i)

                self.bits_extract_hdl_entry_bits_start[i].destroy()
                self.bits_extract_hdl_entry_bits_end[i].destroy()
                self.bits_extract_hdl_entry_rst_hex[i].destroy()
                self.bits_extract_hdl_entry_rst_dec[i].destroy()
                self.bits_extract_hdl_btn_set_val[i].destroy()
                self.bits_extract_hdl_btn_destroy[i].destroy()
                self.bits_extract_hdl_lab_from[i].destroy()
                self.bits_extract_hdl_lab_to[i].destroy()
                self.bits_extract_hdl_lab_hex[i].destroy()
                self.bits_extract_hdl_lab_dec[i].destroy()

                self.bits_extract_hdl_entry_bits_start.pop(i)
                self.bits_extract_hdl_entry_bits_end.pop(i)
                self.bits_extract_hdl_entry_rst_hex.pop(i)
                self.bits_extract_hdl_entry_rst_dec.pop(i)
                self.bits_extract_hdl_btn_set_val.pop(i)
                self.bits_extract_hdl_btn_destroy.pop(i)
                self.bits_extract_hdl_lab_from.pop(i)
                self.bits_extract_hdl_lab_to.pop(i)
                self.bits_extract_hdl_lab_hex.pop(i)
                self.bits_extract_hdl_lab_dec.pop(i)
                break

    def bits_extract_btn_cb_set_val(self, event):
        event.widget['bg'] = bg_to_pressed

        for i in range(0, len(self.bits_extract_pos)):
            if self.bits_extract_hdl_btn_set_val[i]['bg'] == bg_to_pressed:
                s = int(self.bits_extract_pos[i][0].get())
                e = int(self.bits_extract_pos[i][1].get())

                origin_val = get_bits_val(self.dec, s, e)
                hex_val = int(self.bits_extract_rst[i][0].get(), 16)
                dec_val = int(self.bits_extract_rst[i][1].get(), 10)
                if origin_val == hex_val:
                    val = dec_val
                else:
                    val = hex_val

                self.dec = set_bits_val(self.dec, s, e, val)
                self.refresh_all(self.dec)

                self.bits_extract_hdl_btn_set_val[i]['bg'] = bg_zero

    def show_all(self):
        print("show_all")
        self.hex_show.set(self.hex)
        self.dec_show.set(self.dec)
        for i in range(0, 64):
            b_text = str(self.bits[i])
            if self.bits[i]:
                self.button_list[i].configure(text=b_text, bg=bg_one)
            else:
                self.button_list[i].configure(text=b_text, bg=bg_zero)

        for i in range(0, len(self.bits_extract_pos)):
            t_s = self.bits_extract_pos[i][0].get()
            t_e = self.bits_extract_pos[i][1].get()
            if t_s == '' or t_e == '':
                continue

            s = int(t_s)
            e = int(t_e)

            val = get_bits_val(self.dec, s, e)
            self.bits_extract_rst[i][0].set(hex(val))
            self.bits_extract_rst[i][1].set(str(val))

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
            return
        if self.hex_show.get() != '' and int(self.hex_show.get(), 16) != self.dec:
            self.refresh_all(int(self.hex_show.get(), 16))
            return

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

            time.sleep(0.100)

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
get_bits_val(0x345f212, 0, 3)
exit(0)
