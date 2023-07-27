conda create --name sd_3.11 python=3.11 ipykernel

conda activate sd_3.11

python -m ipykernel install --user --name sd_3.11 --display-name "Stable Diffusion with Python 3.11"

# Caution: TensorFlow 2.10 was the last TensorFlow release that supported GPU on native-Windows. Starting with TensorFlow 2.11, you will need to install TensorFlow in WSL2, or install tensorflow-cpu and, optionally, try the TensorFlow-DirectML-Plugin
# TensorFlow 2.10 requires python 3.10 ?
# Ref: 
# - https://www.tensorflow.org/install/pip#windows-native_1
# - https://www.tensorflow.org/install/source_windows#cpu
pip install tensorflow==2.10


pip install accelerate diffusers transformers




# For using Cuda 11.8. See https://pytorch.org/get-started/locally/#anaconda
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118