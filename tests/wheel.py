import time


def start(botshell):
    botshell.sendall("manual_move 750 -750\n".encode())
    time.sleep(5)
    botshell.sendall("manual_move 0 0\n".encode())
    # botshell.sendall("manual_move 100 -100\n".encode())
    # time.sleep(2)
