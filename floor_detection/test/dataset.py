import matplotlib.pyplot as plt
import numpy as np
from src.factory import Factory
from src.dataset import Dataset


def mining():
    factory = Factory(image_shape=(224, 224))
    factory.mining('training')
    factory.mining('validation')


def show_info():
    ds = Dataset(image_shape=(224, 224))
    ds.print_dataset_info()


def view_samples():
    image_shape = (224, 224)
    ds = Dataset(image_shape)
    pl, _ = ds.pipeline()
    num_of_samples = 5
    for raw_imgs, mask_imgs in pl.take(1):
        samples = zip(raw_imgs[:num_of_samples], mask_imgs[:num_of_samples])
        samples = list(samples)
        length = len(samples)
        plt.figure(figsize=(5, 5*length))
        for i, (raw_img, mask_img) in enumerate(samples):
            plt.subplot(length, 2, 2*i+1)
            plt.imshow(raw_img)
            plt.subplot(length, 2, 2*i+2)
            mask_img = np.reshape(mask_img, image_shape)
            plt.imshow(mask_img)
        plt.show()
