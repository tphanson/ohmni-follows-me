import os
import cv2 as cv
import numpy as np

from utils import image, camera
from ohmni.humandetection import HumanDetection
from ohmni.tracker import IdentityTracking

VIDEO0 = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../data/chaplin.mp4")
VIDEO5 = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "../data/MOT17-05-SDP.mp4")


def start(server):
    idtr = IdentityTracking()
    hd = HumanDetection()

    cap = cv.VideoCapture(VIDEO0)
    if (cap.isOpened() == False):
        print("Error opening video stream or file")

    is_first_frames = idtr.tensor_length
    historical_boxes = []
    historical_obj_imgs = []

    while(cap.isOpened()):
        pilimg = camera.fetch(server)
        print(pilimg)
        
        timer = cv.getTickCount()
        ret, frame = cap.read()

        if ret != True:
            break

        img = image.convert_cv_to_pil(frame)
        img = image.resize(img, (640, 480))
        objs = hd.predict(img)

        if len(objs) == 0:
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

            print("==================")
            print(predictions)
            print(predictions[argmax])

        # Test human detection
        # image.draw_objs(img, objs)
        # Test historical frames
        # his_img = None
        # for _img in historical_obj_imgs:
        #     if his_img is None:
        #         his_img = _img
        #     else:
        #         his_img = np.concatenate((his_img, _img), axis=1)
        # cv.imshow('History', his_img)
        # cv.moveWindow('History', 90, 650)

        # img = image.convert_pil_to_cv(img)
        # cv.imshow('Video', img)
        # if cv.waitKey(10) & 0xFF == ord('q'):
        #     break

        # Calculate Frames per second (FPS)
        print("Estimated Time: ", (cv.getTickCount()-timer)/cv.getTickFrequency())
        fps = cv.getTickFrequency() / (cv.getTickCount() - timer)
        print("FPS: {:.1f}".format(fps))
