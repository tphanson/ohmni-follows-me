from __future__ import absolute_import, division, print_function, unicode_literals

import os
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


class Encoder(keras.Model):
    def __init__(self, units):
        super(Encoder, self).__init__()
        self.units = units
        # Recall: in gru cell, h = c
        self.gru = keras.layers.GRU(self.units,
                                    return_sequences=True,
                                    return_state=True,
                                    recurrent_initializer='glorot_uniform')

    def call(self, x, state):
        _, hidden_state = self.gru(x, initial_state=state)
        return hidden_state

    def initialize_hidden_state(self, batch_size):
        return tf.zeros((batch_size, self.units))


class Decoder(keras.Model):
    def __init__(self, units):
        super(Decoder, self).__init__()
        self.gru_units = units[0]
        self.fc_units = units[1]
        self.gru = keras.layers.GRU(self.gru_units,
                                    return_sequences=True,
                                    return_state=True,
                                    recurrent_initializer='glorot_uniform')
        self.fc = keras.layers.Dense(self.fc_units, activation='relu')
        self.classifier = keras.layers.Dense(1, activation='sigmoid')

    def call(self, x, state):
        gru_output, _ = self.gru(x, initial_state=state)
        batch_size, _, _ = gru_output.shape
        gru_output = tf.reshape(gru_output, [batch_size, -1])
        fc_output = self.fc(gru_output)
        classifier_output = self.classifier(fc_output)
        classifier_output = tf.reshape(classifier_output, [-1])
        return classifier_output


class IdentityTracking:
    def __init__(self):
        self.tensor_length = 4
        self.batch_size = 64
        self.image_shape = IMAGE_SHAPE
        self.encoder = Encoder(512)
        self.decoder = Decoder([512, 256])
        self.fextractor = FeaturesExtractor(self.tensor_length, 512)
        self.mextractor = MovementExtractor(self.tensor_length, 256)

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
                                              encoder=self.encoder,
                                              decoder=self.decoder)
        self.checkpoint.restore(
            tf.train.latest_checkpoint(self.checkpoint_dir))

    def formaliza_data(self, obj, frame):
        box = [obj.bbox.xmin/640, obj.bbox.ymin/480,
               obj.bbox.xmax/640, obj.bbox.ymax/480]
        cropped_obj_img = image.crop(frame, obj)
        resized_obj_img = image.resize(cropped_obj_img, self.image_shape)
        obj_img = image.convert_pil_to_cv(resized_obj_img)/255.0
        return box, obj_img

    def predict(self, bboxes_batch, obj_imgs_batch):
        mov_features = self.mextractor(np.array(bboxes_batch))
        cnn_features = self.fextractor(np.array(obj_imgs_batch))
        x = tf.concat([mov_features, cnn_features], 2)
        encoder_input, decoder_input = tf.split(
            x, [self.tensor_length-1, 1], axis=1)
        batch_inputs, _, _ = encoder_input.shape
        init_state = self.encoder.initialize_hidden_state(batch_inputs)
        hidden_state = self.encoder(encoder_input, init_state)
        predictions = self.decoder(decoder_input, hidden_state)

        return predictions, tf.math.argmax(predictions)
