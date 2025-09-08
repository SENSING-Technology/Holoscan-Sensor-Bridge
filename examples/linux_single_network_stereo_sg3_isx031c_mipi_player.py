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
                return 
                
        except Exception as e:
            print(f"Error saving image: {e}")
            import traceback
            traceback.print_exc()


class HoloscanApplication(holoscan.core.Application):
    def __init__(
        self,
        headless,
        cuda_context,
        cuda_device_ordinal,
        hololink_channel_left,
        camera_left,
        hololink_channel_right,
        camera_right,
        camera_mode,
        frame_limit,
        window_height,
        window_width,
        window_title,
    ):
        logging.info("__init__")
        super().__init__()
        self._headless = headless
        self._cuda_context = cuda_context
        self._cuda_device_ordinal = cuda_device_ordinal
        self._hololink_channel_left = hololink_channel_left
        self._camera_left = camera_left
        self._hololink_channel_right = hololink_channel_right
        self._camera_right = camera_right
        self._camera_mode = camera_mode
        self._frame_limit = frame_limit
        self._window_height = window_height
        self._window_width = window_width
        self._window_title = window_title
        # These are HSDK controls-- because we have stereo
        # camera paths going into the same visualizer, don't
        # raise an error when each path present metadata
        # with the same names.  Because we don't use that metadata,
        # it's easiest to just ignore new items with the same
        # names as existing items.
        self.is_metadata_enabled = True
        self.metadata_policy = holoscan.core.MetadataPolicy.REJECT

    def compose(self):
        logging.info("compose")
        if self._frame_limit:
            self._count_left = holoscan.conditions.CountCondition(
                self,
                name="count_left",
                count=self._frame_limit,
            )
            condition_left = self._count_left
            self._count_right = holoscan.conditions.CountCondition(
                self,
                name="count_right",
                count=self._frame_limit,
            )
            condition_right = self._count_right
        else:
            self._ok_left = holoscan.conditions.BooleanCondition(
                self, name="ok_left", enable_tick=True
            )
            condition_left = self._ok_left
            self._ok_right = holoscan.conditions.BooleanCondition(
                self, name="ok_right", enable_tick=True
            )
            condition_right = self._ok_right
        self._camera_left.set_mode(self._camera_mode)
        self._camera_right.set_mode(self._camera_mode)

        # Calculate frame size - UYVY format: width * height * 2 bytes
        frame_size = self._camera_left._width * self._camera_left._height * 2
        frame_context = self._cuda_context
        receiver_operator_left = hololink_module.operators.LinuxReceiverOperator(
            self,
            condition_left,
            name="receiver_left",
            frame_size=frame_size,
            frame_context=frame_context,
            hololink_channel=self._hololink_channel_left,
            device=self._camera_left,
        )
        receiver_operator_right = hololink_module.operators.LinuxReceiverOperator(
            self,
            condition_right,
            frame_size=frame_size,
            frame_context=frame_context,
            hololink_channel=self._hololink_channel_right,
            device=self._camera_right,
        )

        # Add UYVY to RGB conversion operator
        uyvy_converter_left = UYVYToRGBOperator(
            self,
            name="uyvy_converter_left"
        )
        uyvy_converter_right = UYVYToRGBOperator(
            self,
            name="uyvy_converter_right"
        )

        # Add image saving operator
        image_saver_left = ImageSaverOperator(
            self,
            name="image_saver_left",
            save_dir="./captured_images_left"
        )
        image_saver_right = ImageSaverOperator(
            self,
            name="image_saver_right",
            save_dir="./captured_images_right"
        )

        # Set up data flow connections
        self.add_flow(receiver_operator_left, uyvy_converter_left, {("output", "input")})
        self.add_flow(receiver_operator_right, uyvy_converter_right, {("output", "input")})
        self.add_flow(uyvy_converter_left, image_saver_left, {("output", "input")})
        self.add_flow(uyvy_converter_right, image_saver_right, {("output", "input")})


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
        "--window-height",
        type=int,
        default=1552 // 2,  # arbitrary default
        help="Set the height of the displayed window",
    )
    parser.add_argument(
        "--window-width",
        type=int,
        default=2064,  # arbitrary default
        help="Set the width of the displayed window",
    )
    parser.add_argument(
        "--title",
        help="Set the window title",
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
    logging.info(f"{channel_metadata=}")
    # Now make separate connection metadata for left and right; and set them to
    # use sensor 0 and 1 respectively.  This will borrow the data plane
    # configuration we found on that interface.
    channel_metadata_left = hololink_module.Metadata(channel_metadata)
    hololink_module.DataChannel.use_sensor(channel_metadata_left, 0)
    channel_metadata_right = hololink_module.Metadata(channel_metadata)
    hololink_module.DataChannel.use_sensor(channel_metadata_right, 1)
    #
    hololink_channel_left = hololink_module.DataChannel(channel_metadata_left)
    hololink_channel_right = hololink_module.DataChannel(channel_metadata_right)
    
    # Get a handle to the YUV camera
    from hololink.sensors.sg3_isx031c_mipi import sg3_isx031c_mipi
    camera_left = sg3_isx031c_mipi.Isx031Cam(
         hololink_channel_left, expander_configuration=0
    )
    camera_right = sg3_isx031c_mipi.Isx031Cam(
         hololink_channel_right, expander_configuration=0
    )
    
    # Import YUV mode
    from hololink.sensors.sg3_isx031c_mipi import sg3_isx031c_mipi_mode
    camera_mode = sg3_isx031c_mipi_mode.Sensor_Mode(
        args.camera_mode
    )
    
   # What title should we use?
    window_title = f"Holoviz - {args.hololink}"
    if args.title is not None:
        window_title = args.title
    # Set up the application
    application = HoloscanApplication(
        args.headless,
        cu_context,
        cu_device_ordinal,
        hololink_channel_left,
        camera_left,
        hololink_channel_right,
        camera_right,
        camera_mode,
        args.frame_limit,
        args.window_height,
        args.window_width,
        window_title,
    )
    application.config(args.configuration)
    
    # Run it.
    hololink = hololink_channel_left.hololink()
    assert hololink is hololink_channel_right.hololink()
    hololink.start()
    hololink.reset()
    camera_left.setup_clock()  # this also sets camera_right's clock
    camera_left.configure(camera_mode)
    camera_right.configure(camera_mode)

    application.run()
    hololink.stop()

    (cu_result,) = cuda.cuDevicePrimaryCtxRelease(cu_device)
    assert cu_result == cuda.CUresult.CUDA_SUCCESS


if __name__ == "__main__":
    main()