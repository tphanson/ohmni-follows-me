from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import tensorflow as tf
from tensorflow import keras
import numpy as np
import cv2 as cv

from ohmni.mobilenet import Mobilenet

IMAGE_SHAPE = (96, 96)
FEATURE_SHAPE = (3, 3, 1280)
HISTORICAL_LENGTH = 4


class ImageExtractor():
    def __init__(self, tensor_length):
        self.tensor_length = tensor_length
        self.extractor = Mobilenet()

    def call(self, x, training):
        (batch_size, _, _, _, _) = x.shape
        if training:
            x = x.numpy()
        cnn_inputs = np.reshape(
            x, [batch_size*self.tensor_length, IMAGE_SHAPE[0], IMAGE_SHAPE[1], 3])
        extractor_output = self.extractor.predict(cnn_inputs)
        features = tf.reshape(
            extractor_output, [batch_size, self.tensor_length, FEATURE_SHAPE[0], FEATURE_SHAPE[1], FEATURE_SHAPE[2]])
        return features


class FeaturesExtractor(keras.Model):
    def __init__(self, tensor_length, units):
        super(FeaturesExtractor, self).__init__()
        self.fc_units = units
        self.tensor_length = tensor_length
        self.ga = tf.keras.layers.GlobalAveragePooling2D()
        self.fc = keras.layers.Dense(self.fc_units, activation='relu')

    def call(self, x):
        (batch_size, _, _, _, _) = x.shape
        features = tf.reshape(
            x, [batch_size*self.tensor_length, FEATURE_SHAPE[0], FEATURE_SHAPE[1], FEATURE_SHAPE[2]])
        ga_output = self.ga(features)
        fc_output = self.fc(ga_output)
        output = tf.reshape(
            fc_output, [batch_size, self.tensor_length, self.fc_units])
        return output


class MovementExtractor(keras.Model):
    def __init__(self, tensor_length, units):
        super(MovementExtractor, self).__init__()
        self.fc_units = units
        self.tensor_length = tensor_length
        self.fc = keras.layers.Dense(self.fc_units, activation='relu')

    def call(self, x):
        (input_size, _, _) = x.shape
        bbox_inputs = tf.reshape(x, [input_size*self.tensor_length, 4])
        fc_output = self.fc(bbox_inputs)
        features = tf.reshape(
            fc_output, [input_size, self.tensor_length, self.fc_units])
        return features


class IdentityTracking:
    def __init__(self):
        self.tensor_length = HISTORICAL_LENGTH
        self.batch_size = 64
        self.image_shape = IMAGE_SHAPE
        self.iextractor = ImageExtractor(self.tensor_length)
        self.fextractor = FeaturesExtractor(self.tensor_length, 512)
        self.mextractor = MovementExtractor(self.tensor_length, 256)

        self.mymodel = keras.Sequential([
            keras.layers.LSTM(512),
            keras.layers.Dense(512, activation='relu'),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])

        self.optimizer = keras.optimizers.Adam()
        self.loss = keras.losses.BinaryCrossentropy()

        self.loss_metric = keras.metrics.Mean(name='train_loss')
        self.accuracy_metric = keras.metrics.BinaryAccuracy(
            name='train_accurary')

        self.checkpoint_dir = './ohmni/training_checkpoints_' + \
            str(self.image_shape[0]) + '_' + str(self.tensor_length)
        self.checkpoint_prefix = os.path.join(self.checkpoint_dir, 'ckpt')
        self.checkpoint = tf.train.Checkpoint(optimizer=self.optimizer,
                                              fextractor=self.fextractor,
                                              mextractor=self.mextractor,
                                              mymodel=self.mymodel)
        self.checkpoint.restore(
            tf.train.latest_checkpoint(self.checkpoint_dir))

    def formaliza_data(self, obj, frame):
        xmin = 0 if obj.bbox.xmin < 0 else obj.bbox.xmin
        xmax = 300 if obj.bbox.xmax > 300 else obj.bbox.xmax
        ymin = 0 if obj.bbox.ymin < 0 else obj.bbox.ymin
        ymax = 300 if obj.bbox.ymax > 300 else obj.bbox.ymax
        box = [xmin/300, ymin/300, xmax/300, ymax/300]
        if xmin == xmax:
            return np.zeros(self.image_shape)
        if ymin == ymax:
            return np.zeros(self.image_shape)
        cropped_obj_img = frame[ymin:ymax, xmin:xmax]
        resized_obj_img = cv.resize(cropped_obj_img, self.image_shape)
        obj_img = resized_obj_img/255.0
        return box, obj_img

    def predict(self, bboxes_batch, obj_imgs_batch):
        movstart = time.time()
        mov_features = self.mextractor(bboxes_batch)
        movend = time.time()
        print('MOV estimated time {:.4f}'.format(movend-movstart))

        cnnstart = time.time()
        cnn_inputs = self.iextractor.call(
            np.array(obj_imgs_batch, dtype=np.float32), False)
        cnn_features = self.fextractor(cnn_inputs)
        cnnend = time.time()
        print('CNN estimated time {:.4f}'.format(cnnend-cnnstart))

        clstart = time.time()
        x = tf.concat([mov_features, cnn_features], 2)
        clend1 = time.time()
        y = np.array([])
        for i in x:
            y = np.append(y, self.mymodel(tf.convert_to_tensor([i])))
        # y = self.mymodel(x)
        clend2 = time.time()
        print('\t Model {:.4f}'.format(clend2-clend1))
        predictions = tf.reshape(y, [-1])
        clend = time.time()
        print('Classification estimated time {:.4f}'.format(clend-clstart))

        return predictions, tf.math.argmax(predictions)
