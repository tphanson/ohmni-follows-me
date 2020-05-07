# Development Document

## Prerequisites

```
python3 - version 3.6.9
pip3 - version 19.3.1
```

## Install Tensorflow 2.0 for Intel Atom (Optional)

Using built package in `runtime` folder

```
pip3 install tensorflow-2.0.0-cp36-cp36m-linux_x86_64.whl
```

To test env 

```
python3
```

In python sheel,

```
import tensorflow as tf
print(tf.__version__)
```

## Install TFLite

* Doc: https://coral.ai/docs/accelerator/get-started

```
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install libedgetpu1-std
```
Then

```
pip3 install https://dl.google.com/coral/python/tflite_runtime-2.1.0-cp36-cp36m-linux_x86_64.whl
```

## Install dependencies

```
pip3 install opencv-python Pillow
apt update && apt install -y libsm6 libxext6 libxrender1
```

## Debug tracking

Start ROS servers (in tmux)

```
roscore
roslaunch rosbridge_server rosbridge_websocket.launch
rosrun tf2_web_republisher tf2_web_republisher
```

In your machine, you can start rviz to subscribe the topic `/ofm/draw_image/compressed`

```
export ROS_MASTER_URI=<ohmni_ip>:11311
```