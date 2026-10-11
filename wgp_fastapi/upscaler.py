import os
import sys
import time
import uuid
from urllib.request import urlretrieve

import cv2
from PIL import Image

windows_model = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
mac_model = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-macos.zip"
linux_model = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip"

def upscale(image_path, scale_factor):
    print(f"Upscaling {image_path} with factor of x{scale_factor}...")

    if sys.platform == 'darwin':
        executable="realesrgan-ncnn-vulkan"
        urlretrieve(mac_model, "realesrgan-ncnn-vulkan-20220424-macos.zip")
    elif sys.platform == 'linux':
        executable="realesrgan-ncnn-vulkan"
        urlretrieve(linux_model, "realesrgan-ncnn-vulkan-20220424-ubuntu.zip")
    else:
        executable="upscaler\\realesrgan-ncnn-vulkan.exe"
        urlretrieve(windows_model, "realesrgan-ncnn-vulkan-20220424-windows.zip")

    import zipfile
    zip_name = {
        'darwin': "realesrgan-ncnn-vulkan-20220424-macos.zip",
        'linux': "realesrgan-ncnn-vulkan-20220424-ubuntu.zip",
    }.get(sys.platform, "realesrgan-ncnn-vulkan-20220424-windows.zip")
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall("upscaler")

    if sys.platform != 'win32':
        os.system(f"chmod a+x upscaler/{executable}")

    output_file = f"outputs/{str(uuid.uuid4())}.png"

    if sys.platform == 'win32':
        os.system(f"{executable} -i {image_path} -o {output_file} -s {scale_factor}")
    elif os.path.isabs(image_path):
        os.system(f"cd upscaler && ./{executable} -i {image_path} -o ../{output_file} -s {scale_factor}")
    else:
        os.system(f"cd upscaler && ./{executable} -i ../{image_path} -o ../{output_file} -s {scale_factor}")

    # Wait for output file to appear
    timeout = 30
    interval = 0.5
    waited = 0.0
    while not os.path.exists(output_file) and waited < timeout:
        time.sleep(interval)
        waited += interval

    if os.path.exists(output_file):
        print(f"Output file ready: {output_file}")
    else:
        print(f"WARNING: Output file not found after {timeout}s: {output_file}")

    return output_file