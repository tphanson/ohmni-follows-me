import time
import tflite_runtime.interpreter as tflite
import cv2 as cv
import numpy as np
import os

EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
OUTPUT_CHANNELS = 2

class FloorDetection:
        def __init__(self, model_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 
        '../models/tpu/ohmnilabs_floornet_224_quant_postprocess_edgetpu.tflite')):
            self.model_dir = model_dir
            
            self.interpreter = tflite.Interpreter(
                    model_path=self.model_dir,
                    experimental_delegates=[
                        tflite.load_delegate(EDGETPU_SHARED_LIB, {"device": "usb:0"})
                    ])
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            self.image_shape = (
                    self.input_details[0]['shape'][1],
                    self.input_details[0]['shape'][2]
            )

           

        def __summary(self):
            print('*** Input details:', self.input_details)
            print('*** Output details:', self.output_details)


        def __normalize(self, img):
            img = cv.resize(img, self.image_shape)
            return np.array(img/255, dtype=np.float32)


        def __create_mask(self, pred_mask):
            pred_mask = np.argmax(pred_mask, axis=-1)
            pred_mask = pred_mask[..., np.newaxis]
            mask = np.reshape(pred_mask, self.image_shape)
            mask = np.array(mask, dtype=np.float32)
            
            return mask
        
        def infer(self, img):
            self.interpreter.allocate_tensors()
            self.interpreter.set_tensor(self.input_details[0]['index'], [img])
            self.interpreter.invoke()
            feature = self.interpreter.get_tensor(self.output_details[0]['index'])
            return np.array(feature[0], dtype=np.float32)

        def predict(self, img):
            estart = time.time()
            img = self.__normalize(img)
            pred_mask = self.infer(img)
            mask = self.__create_mask(pred_mask)
            eend = time.time()
            
            print('Segmentation estimated time {:.4f}'.format(eend-estart))
            return img, mask


