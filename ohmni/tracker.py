from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import tensorflow as tf
from tensorflow import keras
import tensorflow_hub as hub
import numpy as np

from utils import image

IMAGE_SHAPE = (96, 96)


class FeaturesExtractor(keras.Model):
    def __init__(self, tensor_length, units):
        super(FeaturesExtractor, self).__init__()
        self.fc_units = units
        self.tensor_length = tensor_length
        self.extractor = hub.KerasLayer(
            'https://tfhub.dev/google/imagenet/mobilenet_v2_050_96/feature_vector/4',
            trainable=False,
            input_shape=(IMAGE_SHAPE+(3,))
        )
        self.fc = keras.layers.Dense(self.fc_units, activation='relu')

    def call(self, x):
        (batch_size, _, _, _, _) = x.shape
        cnn_inputs = tf.reshape(
            x, [batch_size*self.tensor_length, IMAGE_SHAPE[0], IMAGE_SHAPE[1], 3])
        logits = self.extractor(cnn_inputs)
        fc_output = self.fc(logits)
        features = tf.reshape(
            fc_output, [batch_size, self.tensor_length, self.fc_units])
        return features


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
        self.tensor_length = 4
        self.batch_size = 64
        self.image_shape = IMAGE_SHAPE
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

        self.checkpoint_dir = './training_checkpoints_' + \
            str(self.image_shape[0]) + '_' + str(self.tensor_length)
        self.checkpoint_prefix = os.path.join(self.checkpoint_dir, 'ckpt')
        self.checkpoint = tf.train.Checkpoint(optimizer=self.optimizer,
                                              fextractor=self.fextractor,
                                              mextractor=self.mextractor,
                                              mymodel=self.mymodel)
        self.checkpoint.restore(
            tf.train.latest_checkpoint(self.checkpoint_dir))

    def formaliza_data(self, obj, frame):
        box = [obj.bbox.xmin/640, obj.bbox.ymin/480,
               obj.bbox.xmax/640, obj.bbox.ymax/480]
        cropped_obj_img = image.crop(frame, obj)
        resized_obj_img = image.resize(cropped_obj_img, self.image_shape)
        obj_img = image.convert_pil_to_cv(resized_obj_img)/255.0
        return box, obj_img

    @tf.function
    def train_step(self, bboxes, cnn_inputs, labels):
        with tf.GradientTape() as tape:
            mov_features = self.mextractor(bboxes)
            cnn_features = self.fextractor(cnn_inputs)
            x = tf.concat([mov_features, cnn_features], 2)
            y = self.mymodel(x)
            predictions = tf.reshape(y, [-1])
            loss = self.loss(labels, predictions)
        variables = self.mymodel.trainable_variables + \
            self.mextractor.trainable_variables + self.fextractor.trainable_variables
        gradients = tape.gradient(loss, variables)
        self.optimizer.apply_gradients(zip(gradients, variables))

        self.loss_metric(loss)
        self.accuracy_metric(labels, predictions)
        return labels, predictions

    def train(self, dataset, epochs=10):
        for epoch in range(epochs):

            start = time.time()
            steps_per_epoch = 0

            iterator = iter(dataset)

            try:
                while True:
                    bboxes, cnn_inputs, labels = next(iterator)
                    steps_per_epoch += 1
                    self.train_step(bboxes, cnn_inputs, labels)
            except StopIteration:
                pass

            self.checkpoint.save(file_prefix=self.checkpoint_prefix)

            end = time.time()
            print('Epoch {}'.format(epoch + 1))
            print('\tSteps per epoch: {}'.format(steps_per_epoch))
            print('\tLoss Metric {:.4f}'.format(self.loss_metric.result()))
            print('\tAccuracy Metric {:.4f}'.format(
                self.accuracy_metric.result()*100))
            print('\tTime taken for 1 epoch {:.4f} sec\n'.format(end - start))

            self.loss_metric.reset_states()
            self.accuracy_metric.reset_states()

    def predict(self, bboxes_batch, obj_imgs_batch):
        movstart = time.time()
        mov_features = self.mextractor(np.array(bboxes_batch))
        movend = time.time()
        print('MOV estimated time {:.4f}'.format(movend-movstart))

        cnnstart = time.time()
        cnn_features = self.fextractor(np.array(obj_imgs_batch))
        cnnend = time.time()
        print('CNN estimated time {:.4f}'.format(cnnend-cnnstart))

        clstart = time.time()
        x = tf.concat([mov_features, cnn_features], 2)
        y = self.mymodel(x)
        predictions = tf.reshape(y, [-1])
        clend = time.time()
        print('Classification estimated time {:.4f}'.format(clend-clstart))

        return predictions, tf.math.argmax(predictions)
