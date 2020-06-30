import cv2
 import zmq
 import base64
 import numpy as np
 
 context = zmq.Context()
 footage_socket = context.socket(zmq.SUB)
 footage_socket.bind('tcp://*:5555')
 footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))
  
 idx=0
 import time
 start_time_get_frame = time.time()
 
 while True:
     frame = footage_socket.recv_string()
     img = base64.b64decode(frame)
     npimg = np.fromstring(img, dtype=np.uint8)
     source = cv2.imdecode(npimg, 1)

     cv2.imshow("Stream", source)

     cv2.imwrite("./oa2/{}.jpg".format(idx), source)
     idx += 1
     if cv2.waitKey(1) & 0xFF == ord('q'):
         break

