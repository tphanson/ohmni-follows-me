import time


def start(botshell):
    print('Testing wheel')

    # botshell.sendall(b'start_autonomy\n')
    # time.sleep(5)
    # print('Start')
    # botshell.sendall(b'follow_me 1 0\n')
    # time.sleep(5)
    # botshell.sendall(b'stop_autonomy\n')
    botshell.sendall("manual_move 3000 -3000\n".encode())
    time.sleep(4)
    botshell.sendall("manual_move 0 0\n".encode())
    time.sleep(1)
    botshell.sendall("manual_move -3000 3000\n".encode())
    time.sleep(4)
    botshell.sendall("manual_move 0 0\n".encode())
    time.sleep(1)
    # botshell.sendall("manual_move -500 500\n".encode())
    # time.sleep(5)
    # botshell.sendall("manual_move 0 0\n".encode())
    # time.sleep(2)
