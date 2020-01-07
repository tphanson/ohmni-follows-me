import sys

import tensorflow as tf
from ohmni import start as ohmni

tf.get_logger().setLevel('ERROR')

if __name__ == "__main__":
    if sys.argv[1] == "--test":
        pass

    elif sys.argv[1] == '--ohmni':
        if sys.argv[2] == 'start':
            ohmni.start()

    else:
        print("Error: Invalid option!")
