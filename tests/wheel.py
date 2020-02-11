import time


def start(botshell):
    botshell.sendall("manual_move 2600 -2400\n".encode())
    time.sleep(1)
    botshell.sendall("manual_move 500 -500\n".encode())
    time.sleep(5)
    botshell.sendall("manual_move 0 0\n".encode())
    time.sleep(2)
    botshell.sendall("manual_move -1000 1000\n".encode())
    time.sleep(5)
    botshell.sendall("manual_move 0 0\n".encode())
    time.sleep(2)
