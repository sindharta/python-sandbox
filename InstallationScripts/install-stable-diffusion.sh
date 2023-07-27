conda create --name sd_3.11 python=3.11 ipykernel

conda activate sd_3.11

python -m ipykernel install --user --name sd_3.11 --display-name "Stable Diffusion with Python 3.11"

pip install tensorflow accelerate diffusers transformers

# For using Cuda 11.8
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118