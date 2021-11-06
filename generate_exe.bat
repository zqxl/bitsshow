::pyinstaller -i ico.ico -F bitsshow.py -w

:: 有窗口
pyinstaller -i ico.ico -F bitsshow.py -c --hidden-import pynput.keyboard.Listener

pause