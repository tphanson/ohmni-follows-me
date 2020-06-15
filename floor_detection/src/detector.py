import time
import tensorflow as tf
from tensorflow import keras
import tflite_runtime.interpreter as tflite
import cv2 as cv
import numpy as np

EDGETPU_SHARED_LIB = 'libedgetpu.so.1'
OUTPUT_CHANNELS = 2


class Detector:
    def __init__(self, image_shape=(128, 128), model_dir=None):
        # Params
        self.image_shape = image_shape
        self.model_dir = model_dir
        # Model
        if self.model_dir is not None:
            # Load pretrained model
            self.model = keras.models.load_model(self.model_dir)
        else:
            # Model stack
            strategy = tf.distribute.MirroredStrategy()
            with strategy.scope():
                # Supportive stacks
                self.base_model = keras.applications.MobileNetV2(
                    input_shape=(self.image_shape+(3,)), include_top=False)
                self.down_stack = self.gen_down_stack()
                self.up_stack = self.gen_up_stack()
                # Main model
                self.model = self.unet_model(OUTPUT_CHANNELS)
                self.optimizer = 'adam'
                self.loss_metric = keras.losses.SparseCategoricalCrossentropy(
                    from_logits=True)
                self.model.compile(optimizer=self.optimizer,
                                   loss=self.loss_metric, metrics=['accuracy'])

    def gen_down_stack(self):
        layer_names = [
            'block_1_expand_relu',   # 112x112
            'block_3_expand_relu',   # 56x56
            'block_6_expand_relu',   # 28x28
            'block_13_expand_relu',  # 14x14
            'block_16_project',      # 7x7
        ]
        layers = [self.base_model.get_layer(
            name).output for name in layer_names]
        down_stack = keras.Model(
            inputs=self.base_model.input, outputs=layers)
        down_stack.trainable = False
        return down_stack

    def upsample(self, filters, size):
        initializer = tf.random_normal_initializer(0., 0.02)
        layer = keras.Sequential()
        layer.add(keras.layers.Conv2DTranspose(filters, size, strides=2,
                                               padding='same',
                                               kernel_initializer=initializer,
                                               use_bias=False))
        layer.add(keras.layers.BatchNormalization())
        layer.add(keras.layers.ReLU())
        return layer

    def gen_up_stack(self):
        up_stack = [
            self.upsample(512, 4),  # 7x7 -> 14x14
            self.upsample(256, 4),  # 14x14 -> 28x28
            self.upsample(128, 4),  # 28x28 -> 56x56
            self.upsample(64, 4),   # 56x56 -> 112x112
        ]
        return up_stack

    def unet_model(self, output_channels):
        inputs = keras.layers.Input(shape=(self.image_shape+(3,)))
        x = inputs
        # Downsampling through the model
        skips = self.down_stack(x)
        x = skips[-1]
        skips = reversed(skips[:-1])
        # Upsampling and establishing the skip connections
        for up, skip in zip(self.up_stack, skips):
            x = up(x)
            concat = keras.layers.Concatenate()
            x = concat([x, skip])
        # This is the last layer of the model (112x112 -> 224x224)
        last = keras.layers.Conv2DTranspose(
            output_channels, 3, strides=2, padding='same')
        x = last(x)
        return keras.Model(inputs=inputs, outputs=x)

    def train(self, ds, epochs, steps_per_epoch, val=None, val_steps=None):
        model_history = self.model.fit(
            ds, epochs=epochs, steps_per_epoch=steps_per_epoch,
            validation_data=val, validation_steps=val_steps
        )
        self.model.save('models')
        return model_history

    def normalize(self, img):
        img = cv.resize(img, self.image_shape)
        return np.array(img/255, dtype=np.float32)

    def create_mask(self, pred_mask):
        pred_mask = np.argmax(pred_mask, axis=-1)
        pred_mask = pred_mask[..., np.newaxis]
        mask = pred_mask[0]
        mask = np.reshape(mask, self.image_shape)
        mask = np.array(mask, dtype=np.float32)
        return mask

    def predict(self, img):
        image_batch = np.array([img], dtype=np.float32)
        pred_mask = self.model.predict(image_batch)
        mask = self.create_mask(pred_mask)
        return mask


class Inference:
    def __init__(self, model_dir):
        self.model_dir = model_dir
        self.interpreter = tflite.Interpreter(
            model_path=self.model_dir,
            experimental_delegates=[
                tflite.load_delegate(EDGETPU_SHARED_LIB)
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
