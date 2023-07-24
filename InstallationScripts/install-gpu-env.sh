conda create --name gpu_env python=3.6 ipykernel

conda activate gpu_env

python -m ipykernel install --user --name gpu_env --display-name "GPU Environment"

pip install tensorflow


# https://docs.nvidia.com/deeplearning/cudnn/install-guide/index.html#install-zlib-windows


# Notes:
# Tensorflow may only be compatible with certain versions of Cuda Toolkit. Check the Anaconda logs if GPU device is not listed
