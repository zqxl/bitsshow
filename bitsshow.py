import tkinter as tk

bg_zero = "#f0f0f0"
bg_one = "#c0c0c0"


class CoreData:
    def __init__(self):
        self.bits = [0 for i in range(0, 64)]
        self.dec = 0
        self.hex = '0x0'

    def refresh_by_dec(self):
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


def refresh_hex(content, reason, name):
    global g_data, hex_show
    g_data.dec = int(content, 16)
    g_data.refresh_by_dec()
    show_all()
    return True


def refresh_hex_button():
    global g_data, hex_show
    refresh_hex(hex_show.get(), 0, 0)


def refresh_dec_button():
    global g_data, dec_show
    refresh_dec(dec_show.get(), 0, 0)


def refresh_dec(content, reason, name):
    global g_data, dec_show
    g_data.dec = int(content, 10)
    g_data.refresh_by_dec()
    show_all()
    return True


def left_shift():
    global dec_show, shift_val
    shift = int(shift_val.get())
    g_data.dec = int(dec_show.get()) << shift
    g_data.refresh_by_dec()
    show_all()


def right_shift():
    global dec_show, shift_val
    shift = int(shift_val.get())
    g_data.dec = int(dec_show.get()) >> shift
    g_data.refresh_by_dec()
    show_all()


def main(root_win):
    global g_data, hex_show, dec_show, button_list, shift_val
    button_width = 1

    root_win.title('bitsshow')

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
    refresh_hex_cmd = root_win.register(refresh_hex)
    entry_hex = tk.Entry(root_win, width=button_width * 18,
                         textvariable=hex_show,
                         validate='focusout',
                         validatecommand=(refresh_hex_cmd, '%P', '%v', '%W'))
    entry_hex.grid(row=4, column=2, columnspan=8, sticky=tk.W)
    entry_hex_b = tk.Button(root_win, text='ok', width=button_width * 2, command=refresh_hex_button)
    entry_hex_b.grid(row=4, column=10, columnspan=2, sticky=tk.W)

    tk.Label(root_win, text='dec:', width=button_width * 4).grid(row=4, column=12, columnspan=2, sticky=tk.E)
    refresh_dec_cmd = root_win.register(refresh_dec)
    entry_dec = tk.Entry(root_win, width=button_width * 18,
                         textvariable=dec_show,
                         validate='focusout',
                         validatecommand=(refresh_dec_cmd, '%P', '%v', '%W'))
    entry_dec.grid(row=4, column=14, columnspan=8, sticky=tk.W)
    entry_dec_b = tk.Button(root_win, text='ok', width=button_width * 2, command=refresh_dec_button)
    entry_dec_b.grid(row=4, column=22, columnspan=2, sticky=tk.W)

    ''' left and right shift '''
    tk.Button(root_win, text='<<', width=2, command=left_shift).grid(row=4, column=25, columnspan=2, sticky=tk.E)
    tk.Entry(root_win, width=2, textvariable=shift_val).grid(row=4, column=27, columnspan=2)
    tk.Button(root_win, text='>>', width=2, command=right_shift).grid(row=4, column=29, columnspan=2, sticky=tk.W)

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
    shift_val = tk.StringVar(root, '01')
    button_list = [tk.Button(root) for x in range(0, 64)]

    g_data = CoreData()

    main(root)
