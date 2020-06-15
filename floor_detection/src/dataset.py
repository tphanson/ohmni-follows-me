import pathlib
import cv2 as cv
import numpy as np
import tensorflow as tf


class Dataset:
    def __init__(self, image_shape=(128, 128), batch_size=64):
        # Paths
        self.rootdir = 'dataset'
        self.datadir = self.rootdir + '/floorNet'
        self.training_set = pathlib.Path(self.datadir + '/training')
        self.validation_set = pathlib.Path(self.datadir + '/validation')
        # Params
        self.image_shape = image_shape
        self.batch_size = batch_size
        # Summary data
        self.num_training, self.num_validation = self.__calculate_data_num()

    def __calculate_data_num(self):
        num_training = int(len(list(self.training_set.glob('*')))/2)
        num_validation = int(len(list(self.validation_set.glob('*')))/2)
        return num_training, num_validation

    def __load_img(self, path, mode='rgb'):
        img = cv.imread(path)
        if mode == 'rgb':
            img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        if mode == 'gray':
            img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        img = cv.resize(img, self.image_shape)
        return img/255

    @tf.function
    def __augment(self, raw_img, mask_img):
        if tf.random.uniform(()) > 0.5:
            raw_img = tf.image.flip_left_right(raw_img)
            mask_img = tf.image.flip_left_right(mask_img)
        return raw_img, mask_img

    def print_dataset_info(self):
        print('*** Number of training data:', self.num_training)
        print('*** Number of validation data:', self.num_validation)

    def load_pair(self, name, mode='training'):
        raw_path = self.datadir+'/'+mode+'/'+name+'.jpg'
        raw_img = self.__load_img(raw_path, 'rgb')
        mask_path = self.datadir+'/'+mode+'/'+name+'_seg.jpg'
        mask_img = self.__load_img(mask_path, 'gray')
        mask_img = np.reshape(mask_img, (mask_img.shape + (1,)))
        return raw_img, mask_img

    def generator(self, mode):
        mode = mode.decode('ascii')
        names = self.num_training if mode == 'training' else self.num_validation
        for i in range(names):
            raw_img, mask_img = self.load_pair(str(i), mode)
            raw_img, mask_img = self.__augment(raw_img, mask_img)
            yield raw_img, mask_img

    def prepare_ds(self, ds, mode='training'):
        if mode == 'training':
            ds = ds.cache()
            ds = ds.shuffle(1024)
            ds = ds.batch(self.batch_size)
            ds = ds.repeat()
            ds = ds.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
        if mode == 'validation':
            ds = ds.batch(self.batch_size)
        return ds

    def pipeline(self):
        # Training dataset
        training_ds = tf.data.Dataset.from_generator(
            self.generator,
            args=['training'],
            output_types=(tf.float32, tf.float32),
            output_shapes=((self.image_shape+(3,)), (self.image_shape+(1,)))
        )
        training_pipeline = self.prepare_ds(training_ds, 'training')
        # validation dataset
        validation_ds = tf.data.Dataset.from_generator(
            self.generator,
            args=['validation'],
            output_types=(tf.float32, tf.float32),
            output_shapes=((self.image_shape+(3,)), (self.image_shape+(1,)))
        )
        validation_pipeline = self.prepare_ds(validation_ds, 'validation')
        return training_pipeline, validation_pipeline
