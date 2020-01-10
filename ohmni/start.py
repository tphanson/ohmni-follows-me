import time
import cv2 as cv

from utils import image, camera
from ohmni.humandetection import HumanDetection
from ohmni.tracker import IdentityTracking

# Open camera:
# monkey -p net.sourceforge.opencamera -c android.intent.category.LAUNCHER 1

# RO: 0.00253 rad/s/unit ; unit: (1,1)
# MOV: 0.43 mm/s/unit ; unit: (1,-1)
MEDIUM_RO = 100
FAST_RO = 300
SLOW_MO = 300
MEDIUM_MO = 500
FAST_MO = 1000


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
        img = image.convert_pil_to_cv(pilimg)
        cv_img = cv.resize(img, (300, 300))
        imgend = time.time()
        print('Image estimated time {:.4f}'.format(imgend-imgstart))

        tpustart = time.time()
        objs = hd.predict(cv_img)
        tpuend = time.time()
        print('TPU estimated time {:.4f}'.format(tpuend-tpustart))

        if len(objs) == 0:
            botshell.sendall("manual_move 0 0\n".encode())
            continue

        if is_first_frames > 0:
            obj_id = 0
            if len(objs) > obj_id:
                is_first_frames -= 1
                box, obj_img = idtr.formaliza_data(objs[obj_id], cv_img)
                historical_boxes.append(box)
                historical_obj_imgs.append(obj_img)
            continue
        else:
            bboxes_batch = []
            obj_imgs_batch = []

            for obj in objs:
                box, obj_img = idtr.formaliza_data(obj, cv_img)
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

                # Drive car
                xmed = (obj.bbox.xmin + obj.bbox.xmax)/2
                area = (obj.bbox.xmax-obj.bbox.xmin) * \
                    (obj.bbox.ymax-obj.bbox.ymin)
                print('*** XMED:', xmed)
                print('*** AREA:', area)
                if xmed < 60:
                    # Fast Left
                    botshell.sendall(
                        f"manual_move -{FAST_RO} -{FAST_RO}\n".encode())
                elif xmed < 120:
                    # Medium Left
                    botshell.sendall(
                        f"manual_move -{MEDIUM_RO} -{MEDIUM_RO}\n".encode())
                elif xmed > 240:
                    # Fast Right
                    botshell.sendall(
                        f"manual_move {FAST_RO} {FAST_RO}\n".encode())
                elif xmed > 180:
                    # Medium Right
                    botshell.sendall(
                        f"manual_move {MEDIUM_RO} {MEDIUM_RO}\n".encode())
                elif area > 30000:
                    # Medium Backward
                    botshell.sendall(
                        f"manual_move -{MEDIUM_MO} {MEDIUM_MO}\n".encode())
                elif area < 10000:
                    # Fast Forward
                    botshell.sendall(
                        f"manual_move {FAST_MO} -{FAST_MO}\n".encode())
                elif area < 15000:
                    # Medium Forward
                    botshell.sendall(
                        f"manual_move {MEDIUM_MO} -{MEDIUM_MO}\n".encode())
                elif area < 20000:
                    # Slow Forward
                    botshell.sendall(
                        f"manual_move {SLOW_MO} -{SLOW_MO}\n".encode())
                else:
                    # Stop
                    botshell.sendall("manual_move 0 0\n".encode())

            print("==================")
            print(predictions)
            print(predictions[argmax])

        # Calculate Frames per second (FPS)
        print("Total Estimated Time: ",
              (cv.getTickCount()-timer)/cv.getTickFrequency())
        fps = cv.getTickFrequency() / (cv.getTickCount() - timer)
        print("FPS: {:.1f}".format(fps))
