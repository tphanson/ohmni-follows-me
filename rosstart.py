#!/usr/bin/env python3

import socket
from ohmni import start as ohmni


if __name__ == "__main__":
    # Init botshell
    botshell = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    botshell.connect("/app/bot_shell.sock")
    botshell.sendall(b"wake_head\n")
    ohmni.start(botshell)
