# Holoscan Sensor Bridge

## Introduction

Holoscan Sensor Bridge provides a FPGA based interface for low-latency sensor data
processing using GPUs. Peripheral device data is acquired by the FPGA and sent via UDP
to the host system where ConnectX devices can write that UDP data directly into GPU
memory. 
This software package based on nvidia official HSB v2.2.1 package and add supports for SENSING HSB cameras with 
[Lattice Holoscan Sensor Bridge device](https://www.latticesemi.com/products/developmentboardsandkits/certuspro-nx-sensor-to-ethernet-bridge-board)

## Setup

Holoscan sensor bridge software comes with an
[extensive user guide](https://docs.nvidia.com/holoscan/sensor-bridge/latest/),
including instructions for setup on
[NVIDIA IGX](https://www.nvidia.com/en-us/edge-computing/products/igx/) and
[NVIDIA AGX](https://developer.nvidia.com/embedded/learn/jetson-agx-orin-devkit-user-guide/index.html)
configurations. Please see the user guide for host configuration and instructions on
running unit tests.

## Use With SENSING HSB MIPI Cameras

This software package add supports for following SENSING HSB cameras:

| Camera                          | Description               |
| :------------------------------ | ------------------------- |
| sg2_ar0234c_mipi                | 2MP RAW Camera            |
| sg3_isx031c_mipi                | 3MP YUV Camera            |
| sg8_imx678c_mipi                | 8MP RAW Camera            |

Currently supported for use on Jetson Agx Orin Devkit with Jetpack 6.0 or later

### Use with Jetson Agx Orin Devkit

1. **SENSING will provide the following accessorie**

    - Jetson Agx Orin Devkit (Provided By SENSING Or Use Your Own)
    - Holoscan Sensor Bridge Board with SENSING MIPI Camera Adapter
    - SENSING HSB MIPI Cameras
    - FPC Cable
    - RJ45 Ethernet Cable
    - RJ45 to SFP converter
    - Power adapter

    <p align="center">
        <img src="./docs/user_guide/images/SENSING_HSB_Cameras/07.jpg" width="90%" />
    </p>

2. **Connect HSB MIPI Camera Onto Holoscan Sensor Bridge Board**

    - Connect FPC Cable With HSB MIPI Camera

    <p align="center">
        <img src="./docs/user_guide/images/SENSING_HSB_Cameras/02.jpg" width="90%" />
    </p>

    - Fixed to the Holoscan Sensor Bridge Board

    <p align="center">
        <img src="./docs/user_guide/images/SENSING_HSB_Cameras/05.jpg" width="90%" />
    </p>

3. **Connect all to Jetson Agx Orin Devkit**


    - Currently, only single MIPI cameras can be accepted.(CN1)
    <p align="center">
        <img src="./docs/user_guide/images/SENSING_HSB_Cameras/01.jpg" width="90%" />
    </p>

3. **Power Supply**

    - Provide 12v power supply to the Jetson AGX Orin DevKit
    - Provide 12v power supply to the Holoscan Sensor Bridge Board (A Type-C Power Supply)
    - Provide 12v power supply to the SENSING MIPI Camera Adapter On Holoscan Sensor Bridge Board

4. **Boot system and Bringup camera**

    - Please first complete the "Host Setup" described on [extensive user guide](https://docs.nvidia.com/holoscan/sensor-bridge/latest/)
    - Clone this software package onto device
    - Enter the software package path and execute the command "sh docker/build.sh -igpu" to build the Holoscan Sensor Bridge container
    - Execute the following command at the device terminal to getinto the demo container
        ```
        xhost +
        sh docker/demo.sh
        ```
    - Execute the following command to bringup SENSING MIPI Camera
        
        - For sg2_ar0234c_mipi
            ```
            python3 examples/linux_sg2_ar0234c_mipi_player.py 
            ```
        - For sg3_isx031c_mipi
            
            *note* : only capturing image data and saving pictures are supported, and pictures will save to "captured_images" folder
            ```
            python3 examples/linux_sg3_isx031c_mipi_capture.py
            ```
        - For sg8_imx678c_mipi
            ```
            python3 examples/linux_sg8_imx678c_mipi_player.py
            ```