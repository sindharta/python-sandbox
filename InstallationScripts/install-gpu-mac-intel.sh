conda create --name gpu_3.8 python=3.8 ipykernel

conda activate gpu_3.8

python -m ipykernel install --user --name gpu_3.8 --display-name "GPU with Python 3.8"

# SYSTEM_VERSION_COMPAT=0 to bypass version compatibility issue
SYSTEM_VERSION_COMPAT=0 pip install tensorflow-macos tensorflow-metal


