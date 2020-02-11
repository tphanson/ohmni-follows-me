import time


def start(botshell):
    botshell.sendall("manual_move 2000 -1800\n".encode())
    time.sleep(3)
    botshell.sendall("manual_move 500 -500\n".encode())
    time.sleep(5)
    botshell.sendall("manual_move 0 0\n".encode())
    time.sleep(2)
    botshell.sendall("manual_move -1500 1500\n".encode())
    time.sleep(5)
    botshell.sendall("manual_move 0 0\n".encode())
    time.sleep(2)
