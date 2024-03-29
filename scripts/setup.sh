#!/bin/bash

# Exit when any installment failed.
set -e

# Upgrade system
sudo apt-get update

# Install pip3
sudo apt-get install -y python3-pip
sudo -H pip3 install --upgrade pip
# Install dependencies
pip3 install -r requirements.txt

# Install TF Lite
pip3 install https://dl.google.com/coral/python/tflite_runtime-2.1.0-cp36-cp36m-linux_x86_64.whl

# Install edgetpu
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y libedgetpu1-std
sudo apt-get install -y python3-edgetpu
apt update && apt install -y libsm6 libxext6 libxrender1
