#!/bin/bash

# Exit when any installment failed.
set -e

# Upgrade system
sudo apt-get update

# Install pip3
sudo apt-get install -y python3-pip
sudo -H pip3 install --upgrade pip

# Install TF 2.0 for Intel Atom
cd ./runtime
pip3 install tensorflow-2.0.0-cp36-cp36m-linux_x86_64.whl

# Install TF Lite
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y libedgetpu1-std
pip3 install tflite_runtime-1.14.0-cp36-cp36m-linux_x86_64.whl

# Install dependencies
pip3 install opencv-python Pillow
apt update && apt install -y libsm6 libxext6 libxrender1
pip3 install "tensorflow_hub>=0.6.0"