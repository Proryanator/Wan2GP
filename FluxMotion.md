# FluxMotion Server

This is an API wrapper that calls the logic in Wan2GP, and is meant to be easily interfaced with by the FluxMotion iOS/Android app.

## System Requirements

The server will download models on-demand when you first use a feature, rather than downloading everything up front. This reduces the initial setup time and disk space requirements.

### Windows 10 or Windows 11
You will get all the features of this app working out the box so long as you have:

- an Nvidia GPU with at least 12GB of VRAM, 1000-5000 series
- System RAM: 32GB required
- ~150GB of space available (models are downloaded when you use them, and they total up to 130GB or so of space) 

### macOS
You need at least 32GB of RAM to run FluxMotion server on macOS. With a Mac that has integrated GPU and 36GB+ VRAM, you should be able to do text to image and image editing features. For image to video, you may be limited to lower resolutions and shorter durations.

- a Mac powered by an Apple Silicon Chip (M1 or greater)
- 32GB of RAM or more

## Installation Instructions (Windows)

1. Download the source code for this repo as a [.zip](https://github.com/Proryanator/Wan2GP/archive/refs/heads/main.zip) or clone the repo via git
1. If you downloaded the .zip, unzip it to a folder called `Wan2GP` on your fastest drive (to make sure models load quickly). SSD is recommended
1. Double-click the `setup.bat` file to set up the python environment and all that you need to run the server. _Please be patient; there is a lot to install here_
1. When that is done, double-click `run.bat` to start the server
1. In the logs of the command line prompt, you should see `It will be accessible on your network at: http://<ip_address>:8888`. Please enter the ip address listed there into your FluxMotion app and tap on 'Connect'. You may need to allow for local network permissions on your device, and retry tapping 'Connect'.
1. If it all worked, you'll see a green checkmark next to the 'Connect' button in the FluxMotion app. 

## Installation Instructions (macOS)
1. Download the source code for this repo as a [.zip](https://github.com/Proryanator/Wan2GP/archive/refs/heads/main.zip) or clone the repo via git
1. If you downloaded the .zip, unzip it to a folder called `Wan2GP` on your fastest drive (to make sure models load quickly). SSD is recommended
1. Run the `setup.sh` file to set up the python environment and all that you need to run the server. _Please be patient; there is a lot to install here_
1. If the server does not start on it's own, then run `run.sh` and you are good to go 
1. In the logs of the terminal, you should see `It will be accessible on your network at: http://<ip_address>:8888`. Please enter the ip address listed there into your FluxMotion app and tap on 'Connect'. You may need to allow for local network permissions on your device, and retry tapping 'Connect'.
1. If it all worked, you'll see a green checkmark next to the 'Connect' button in the FluxMotion app.

## Updating the server (Windows and Mac)

Simply run the `update.bat` if on Windows, or `update.sh` if on mac. It will update the source code in place and re-create your environment.

If you run into any issues during the environment re-creation with miniconda, you may need to delete the conda environment and retry (for Windows this is `C:\Miniconda3` and mac is `/Users/<you>/miniconda`).

## Uninstallation (Windows)

1. Delete the `C:\Miniconda3` folder (this was created for you automatically during installation)
1. Delete the `Wan2GP` folder that you downloaded; this also deletes the models 

## Uninstallation (macOS)

1. Delete the `/Users/<you>/miniconda` folder (this was created for you automatically during installation)
1. Delete the `Wan2GP` folder that you downloaded; this also deletes the models

### Troubleshooting

#### Out of Memory Errors or Failure During Generation

Depending on the performance mode you run with, i.e. `Ultra Speed` or `Speed` or `Quality` a different sized model will be used for images. Video uses the same model regardless.

It is possible that a combination of your GPU's VRAM or system RAM is not enough for the server to allocate the model. If you are not able to run at least `Ultra Speed` image generation, unfortunately you will not be able to run the models on your local computer.

#### Not Enough Disk Space

If you plan on using all models and modes, it requires about `130GB` of disk space. Models are now downloaded on-demand when you first use a feature.

#### Any Other Issues

If you get any errors during install, please open up an [issue](https://github.com/Proryanator/Wan2GP/issues) on this repo and the author will try to address it for you.