import time
import cv2 as cv

from utils import image, camera
from ohmni.humandetection import HumanDetection
from ohmni.tracker import IdentityTracking

RO = 110
MO = 320


def start(server, botshell):
    idtr = IdentityTracking()
    hd = HumanDetection()

    is_first_frames = idtr.tensor_length
    historical_boxes = []
    historical_obj_imgs = []

    while(True):
        pilimg = camera.fetch(server)

        if pilimg is None:
            continue

        timer = cv.getTickCount()

        imgstart = time.time()
        img = image.resize(pilimg, (640, 480))
        imgend = time.time()
        print('Image estimated time {:.4f}'.format(imgend-imgstart))

        tpustart = time.time()
        objs = hd.predict(img)
        tpuend = time.time()
        print('TPU estimated time {:.4f}'.format(tpuend-tpustart))

        if len(objs) == 0:
            botshell.sendall("manual_move 0 0\n".encode())
            continue

        if is_first_frames > 0:
            obj_id = 0
            if len(objs) > obj_id:
                is_first_frames -= 1
                box, obj_img = idtr.formaliza_data(objs[obj_id], img)
                historical_boxes.append(box)
                historical_obj_imgs.append(obj_img)
            continue
        else:
            bboxes_batch = []
            obj_imgs_batch = []

            for obj in objs:
                box, obj_img = idtr.formaliza_data(obj, img)
                boxes_tensor = historical_boxes.copy()
                boxes_tensor.pop(0)
                boxes_tensor.append(box)
                obj_imgs_tensor = historical_obj_imgs.copy()
                obj_imgs_tensor.pop(0)
                obj_imgs_tensor.append(obj_img)
                bboxes_batch.append(boxes_tensor)
                obj_imgs_batch.append(obj_imgs_tensor)

            predictions, argmax = idtr.predict(bboxes_batch, obj_imgs_batch)
            predictions = predictions.numpy()
            argmax = argmax.numpy()
            if predictions[argmax] >= 0.7:
                obj = objs[argmax]
                historical_boxes = bboxes_batch[argmax].copy()
                historical_obj_imgs = obj_imgs_batch[argmax].copy()
                image.draw_objs(img, [obj])

                # Drive car
                xmed = (obj.bbox.xmin + obj.bbox.xmax)/2
                area = (obj.bbox.xmax-obj.bbox.xmin) * \
                    (obj.bbox.ymax-obj.bbox.ymin)
                if xmed < 200:
                    # Turn left
                    botshell.sendall(f"manual_move -{RO} -{RO}\n".encode())
                elif xmed > 440:
                    # Turn right
                    botshell.sendall(f"manual_move {RO} {RO}\n".encode())
                elif area > 100000:
                    # Backward
                    botshell.sendall(f"manual_move -{MO} {MO}\n".encode())
                elif area < 70000:
                    # Forward
                    botshell.sendall(f"manual_move {MO} -{MO}\n".encode())
                else:
                    # Stop
                    botshell.sendall("manual_move 0 0\n".encode())

            print("==================")
            print(predictions)
            print(predictions[argmax])

        if cv.waitKey(10) & 0xFF == ord('q'):
            break

        # Calculate Frames per second (FPS)
        print("Total Estimated Time: ",
              (cv.getTickCount()-timer)/cv.getTickFrequency())
        fps = cv.getTickFrequency() / (cv.getTickCount() - timer)
        print("FPS: {:.1f}".format(fps))
