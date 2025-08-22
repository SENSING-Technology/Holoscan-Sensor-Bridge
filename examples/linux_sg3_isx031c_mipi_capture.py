# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import ctypes
import logging
import os
import time
import sys

import holoscan
from cuda import cuda
import cv2
import numpy as np

import hololink as hololink_module

# Import UYVY to RGB conversion operator
from uyvy_converter_capture import UYVYToRGBOperator


class ImageSaverOperator(holoscan.core.Operator):
    def __init__(self, fragment, name="image_saver", save_dir="./captured_images"):
        super().__init__(fragment, name)
        self.save_dir = save_dir
        self.frame_count = 0
        
        # Create output directory
        os.makedirs(save_dir, exist_ok=True)
        
    def setup(self, spec):
        spec.input("input")
    
    def compute(self, op_input, op_output, context):
        try:
            # Receive image data
            image_data = op_input.receive("input")
            self.frame_count += 1
            
            # Extract numpy array
            if hasattr(image_data, 'asnumpy'):
                img_np = image_data.asnumpy()
            elif isinstance(image_data, dict):
                # Extract data from dictionary
                if len(image_data) > 0:
                    first_key = list(image_data.keys())[0]
                    actual_data = image_data[first_key]
                    if hasattr(actual_data, 'asnumpy'):
                        img_np = actual_data.asnumpy()
                    else:
                        img_np = np.asarray(actual_data)
                else:
                    img_np = np.zeros((1536, 1920, 4), dtype=np.uint8)
            else:
                img_np = np.asarray(image_data)
            
            print(f"Saving frame {self.frame_count}: image shape {img_np.shape}, dtype {img_np.dtype}")
            
            # Save image
            if len(img_np.shape) == 3:
                if img_np.shape[2] == 4:  # RGBA
                    # Convert to BGR for saving
                    bgr_img = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
                    filename = os.path.join(self.save_dir, f"frame_{self.frame_count:04d}.png")
                    cv2.imwrite(filename, bgr_img)
                    print(f"Saved RGBA image: {filename}")
                elif img_np.shape[2] == 3:  # RGB
                    # Convert to BGR for saving
                    bgr_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                    filename = os.path.join(self.save_dir, f"frame_{self.frame_count:04d}.png")
                    cv2.imwrite(filename, bgr_img)
                    print(f"Saved RGB image: {filename}")
            elif len(img_np.shape) == 2:  # Grayscale
                filename = os.path.join(self.save_dir, f"frame_{self.frame_count:04d}.png")
                cv2.imwrite(filename, img_np)
                print(f"Saved grayscale image: {filename}")
            
            # Limit number of saved frames to avoid filling up disk
            if self.frame_count >= 10:
                print("10 frames saved, exiting program")
                sys.exit(0)
                
        except Exception as e:
            print(f"Error saving image: {e}")
            import traceback
            traceback.print_exc()


class HoloscanApplication(holoscan.core.Application):
    def __init__(
        self,
        headless,
        fullscreen,
        cuda_context,
        cuda_device_ordinal,
        hololink_channel,
        camera,
        camera_mode,
        frame_limit,
    ):
        logging.info("__init__")
        super().__init__()
        self._headless = headless
        self._fullscreen = fullscreen
        self._cuda_context = cuda_context
        self._cuda_device_ordinal = cuda_device_ordinal
        self._hololink_channel = hololink_channel
        self._camera = camera
        self._camera_mode = camera_mode
        self._frame_limit = frame_limit

    def compose(self):
        logging.info("compose")
        if self._frame_limit:
            self._count = holoscan.conditions.CountCondition(
                self,
                name="count",
                count=self._frame_limit,
            )
            condition = self._count
        else:
            self._ok = holoscan.conditions.BooleanCondition(
                self, name="ok", enable_tick=True
            )
            condition = self._ok
        self._camera.set_mode(self._camera_mode)

        # Calculate frame size - UYVY format: width * height * 2 bytes
        frame_size = self._camera._width * self._camera._height * 2
        frame_context = self._cuda_context
        receiver_operator = hololink_module.operators.LinuxReceiverOperator(
            self,
            condition,
            name="receiver",
            frame_size=frame_size,
            frame_context=frame_context,
            hololink_channel=self._hololink_channel,
            device=self._camera,
        )

        # Add UYVY to RGB conversion operator
        uyvy_converter = UYVYToRGBOperator(
            self,
            name="uyvy_converter"
        )

        # Add image saving operator
        image_saver = ImageSaverOperator(
            self,
            name="image_saver",
            save_dir="./captured_images"
        )

        # Set up data flow connections
        self.add_flow(receiver_operator, uyvy_converter, {("output", "input")})
        self.add_flow(uyvy_converter, image_saver, {("output", "input")})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--camera-mode",
        type=int,
        default=0,  # YUV mode
        help="YUV Camera mode",
    )
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument(
        "--fullscreen", action="store_true", help="Run in fullscreen mode"
    )
    parser.add_argument(
        "--frame-limit",
        type=int,
        default=10,  # Limit to 10 frames
        help="Exit after receiving this many frames",
    )
    default_configuration = os.path.join(
        os.path.dirname(__file__), "example_configuration.yaml"
    )
    parser.add_argument(
        "--configuration",
        default=default_configuration,
        help="Configuration file",
    )
    parser.add_argument(
        "--hololink",
        default="192.168.0.2",
        help="IP address of Hololink board",
    )
    parser.add_argument(
        "--log-level",
        type=int,
        default=20,
        help="Logging level to display",
    )
    parser.add_argument(
        "--expander-configuration",
        type=int,
        default=0,
        choices=(0, 1, 2, 4, 8),
        help="I2C Expander configuration",
    )
    args = parser.parse_args()
    hololink_module.logging_level(args.log_level)
    logging.info("Initializing.")
    
    # Get a handle to the GPU
    (cu_result,) = cuda.cuInit(0)
    assert cu_result == cuda.CUresult.CUDA_SUCCESS
    cu_device_ordinal = 0
    cu_result, cu_device = cuda.cuDeviceGet(cu_device_ordinal)
    assert cu_result == cuda.CUresult.CUDA_SUCCESS
    cu_result, cu_context = cuda.cuDevicePrimaryCtxRetain(cu_device)
    assert cu_result == cuda.CUresult.CUDA_SUCCESS
    
    # Get a handle to the Hololink device
    channel_metadata = hololink_module.Enumerator.find_channel(channel_ip=args.hololink)
    hololink_channel = hololink_module.DataChannel(channel_metadata)
    
    # Get a handle to the YUV camera
    from hololink.sensors.sg3_isx031c_mipi import sg3_isx031c_mipi
    camera = sg3_isx031c_mipi.Isx031Cam(
        hololink_channel, expander_configuration=args.expander_configuration
    )
    
    # Import YUV mode
    from hololink.sensors.sg3_isx031c_mipi import sg3_isx031c_mipi_mode
    camera_mode = sg3_isx031c_mipi_mode.Sensor_Mode(
        args.camera_mode
    )
    
    # Set up the application
    application = HoloscanApplication(
        args.headless,
        args.fullscreen,
        cu_context,
        cu_device_ordinal,
        hololink_channel,
        camera,
        camera_mode,
        args.frame_limit,
    )
    application.config(args.configuration)
    
    # Run it.
    hololink = hololink_channel.hololink()
    hololink.start()
    hololink.reset()
    camera.setup_clock()
    camera.configure(camera_mode)
    application.run()
    hololink.stop()

    (cu_result,) = cuda.cuDevicePrimaryCtxRelease(cu_device)
    assert cu_result == cuda.CUresult.CUDA_SUCCESS


if __name__ == "__main__":
    main()