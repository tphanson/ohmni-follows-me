import os
import datetime
import time
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from src.detector import Detector, Inference
from src.dataset import Dataset
from utils.camera import Camera


def mobilenet():
    image_shape = (224, 224)
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(image_shape+(3,)), include_top=False)
    print(base_model.summary())


def summary():
    detector = Detector(image_shape=(224, 224))
    tf.keras.utils.plot_model(detector.model, show_shapes=True)
    img = cv.imread('model.png')
    img = cv.resize(img, (512, 768))
    cv.imshow('Model summary', img)
    cv.waitKey()


def __display(display_list):
    plt.figure(figsize=(15, 15))
    title = ['Input Image', 'True Mask', 'Predicted Mask']
    for i in range(len(display_list)):
        plt.subplot(1, len(display_list), i+1)
        plt.title(title[i])
        plt.imshow(tf.keras.preprocessing.image.array_to_img(display_list[i]))
        plt.axis('off')
    plt.show()


def __create_mask(pred_mask):
    pred_mask = np.argmax(pred_mask, axis=-1)
    pred_mask = pred_mask[..., np.newaxis]
    return pred_mask[0]


def show_predictions():
    image_shape = (224, 224)
    detector = Detector(image_shape)
    ds = Dataset(image_shape)
    pipeline, _ = ds.pipeline()
    for image, mask in pipeline.take(1):
        pred_mask = detector.predict(image)
        __display([image[0], mask[0], __create_mask(pred_mask)])


def train():
    # Config params
    image_shape = (224, 224)
    batch_size = 64
    epochs = 30
    # Dataset & model
    detector = Detector(image_shape)
    ds = Dataset(image_shape, batch_size)
    training_pipeline, validation_pipeline = ds.pipeline()
    steps_per_epoch = ds.num_training//batch_size
    # Start training
    model_history = detector.train(
        training_pipeline, epochs, steps_per_epoch,
        validation_pipeline,
    )
    # Visualize loss
    loss = model_history.history['loss']
    val_loss = model_history.history['val_loss']
    range_of_epochs = range(epochs)
    plt.figure()
    plt.plot(range_of_epochs, loss, 'r', label='Training loss')
    plt.plot(range_of_epochs, val_loss, 'bo', label='Validation loss')
    plt.title('Training Loss and Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss Value')
    plt.ylim([0, 1])
    plt.legend()
    plt.show()


def predict():
    # Config
    image_shape = (224, 224)
    output_shape = (640, 480)
    alpha = 0.5
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = cv.VideoWriter(
        'dist/floorNet-%s.avi' % current_time, cv.VideoWriter_fourcc(*'DIVX'), 10, output_shape)
    # Model
    detector = Detector(image_shape, 'models')
    # Image source
    cam = Camera()
    stream = cam.get_stream()
    # Prediction
    while True:
        start = time.time()
        print("======================================")

        img = stream.get()
        img = detector.normalize(img)
        mask = detector.predict(img)
        mask = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
        cv.addWeighted(mask, alpha, img, 1-alpha, 0, img)
        img = cv.resize(img, output_shape)
        cv.imshow('Camera', img)

        # Save video
        frame = (img*255).astype(np.uint8)
        out.write(frame)

        # Calculate frames per second (FPS)
        end = time.time()
        print('Total estimated time: {:.4f}'.format(end-start))
        fps = 1/(end-start)
        print("FPS: {:.1f}".format(fps))

        if cv.waitKey(10) & 0xFF == ord('q'):
            break
    # Clear resources
    out.release()
    cv.destroyAllWindows()
    cam.terminate()


def convert():
    # Load model
    image_shape = (224, 224)
    detector = Detector(image_shape, 'models')
    model = detector.model
    # Data pipeline
    batch_size = 64
    ds = Dataset(image_shape, batch_size)
    pipeline, _ = ds.pipeline()

    def representative_dataset_gen():
        for tensor in pipeline.take(1):
            raw_imgs, mask_imgs = tensor
            img = np.array([raw_imgs[0]])
            yield [img]  # Shape (1, height, width, channel)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.uint8
    converter.inference_output_type = tf.uint8
    tflite_quant_model = converter.convert()

    MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '../models/tpu/ohmnilabs_floornet_224_quant_postprocess.tflite')
    open(MODEL, 'wb').write(tflite_quant_model)


def infer():
    # Image source
    cam = Camera()
    stream = cam.get_stream()
    # Load edge model
    EDGE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '../models/tpu/ohmnilabs_floornet_224_quant_postprocess_edgetpu.tflite')
    inference = Inference(EDGE_MODEL)
    # Prediction
    while True:
        start = time.time()
        print("======================================")
        # Infer
        raw_img = stream.get()
        img, mask = inference.predict(raw_img)
        # Visualize
        mask = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
        cv.addWeighted(mask, 0.5, img, 0.5, 0, img)
        cv.imshow('Camera', img)

        # Calculate frames per second (FPS)
        end = time.time()
        print('Total estimated time: {:.4f}'.format(end-start))
        fps = 1/(end-start)
        print("FPS: {:.1f}".format(fps))

        if cv.waitKey(10) & 0xFF == ord('q'):
            break
    # Clear resources
    cv.destroyAllWindows()
    cam.terminate()
