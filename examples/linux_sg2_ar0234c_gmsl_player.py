# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# See README.md for detailed information.

import argparse
import ctypes
import logging
import os
import time

import holoscan
from cuda import cuda

import hololink as hololink_module

class TimestampPrinterOp(holoscan.core.Operator):
    """Custom operator to print timestamps from tensor metadata."""

    def __init__(self, fragment, *args, name="timestamp_printer", **kwargs):
        self.camera_name = kwargs.pop("camera_name", "unknown")
        super().__init__(fragment, *args, name=name, **kwargs)
        self.frame_count = 0

    def setup(self, spec):
        spec.input("input")
        spec.output("output")

    def compute(self, op_input, op_output, context):
        message = op_input.receive("input")
        self.frame_count += 1
        timestamp_s = self.metadata.get("timestamp_s", 0)
        timestamp_ns = self.metadata.get("timestamp_ns", 0)
        total_seconds = timestamp_s + timestamp_ns / 1_000_000_000.0
        logging.info(
            f"[{self.camera_name}] Frame {self.frame_count}: "
            f"timestamp={total_seconds:.9f}"
        )
        op_output.emit(message, "output")

class HoloscanApplication(holoscan.core.Application):
    def __init__(
        self,
        headless,
        fullscreen,
        cuda_context,
        cuda_device_ordinal,
        positions,
        hololink_channels,
        cameras,
        camera_mode,
        frame_limit,
        window_height,
        window_width,
        print_time,
    ):
        logging.info("__init__")
        super().__init__()
        self._headless = headless
        self._fullscreen = fullscreen
        self._cuda_context = cuda_context
        self._cuda_device_ordinal = cuda_device_ordinal
        self._positions = positions
        self._hololink_channels = hololink_channels
        self._cameras = cameras
        self._camera_mode = camera_mode
        self._frame_limit = frame_limit
        self._window_height = window_height
        self._window_width = window_width
        self._print_time = print_time
        # These are HSDK controls
        self.is_metadata_enabled = True
        self.metadata_policy = holoscan.core.MetadataPolicy.REJECT

    def compose(self):
        logging.info("compose")

        VIEW_LAYOUTS = {
            "front": (0.0, 0.0, 0.5, 0.5),
            "back":  (0.5, 0.0, 0.5, 0.5),
            "left":  (0.0, 0.5, 0.5, 0.5),
            "right": (0.5, 0.5, 0.5, 0.5),
        }
        tensors = []
        for pos in self._positions:
            if pos not in VIEW_LAYOUTS:
                raise ValueError(f"Unsupported camera position for display: {pos}")
            offset_x, offset_y, width, height = VIEW_LAYOUTS[pos]
            spec = holoscan.operators.HolovizOp.InputSpec(
                pos,
                holoscan.operators.HolovizOp.InputType.COLOR
            )
            view = holoscan.operators.HolovizOp.InputSpec.View()
            view.offset_x = offset_x
            view.offset_y = offset_y
            view.width = width
            view.height = height
            spec.views = [view]
            tensors.append(spec)
        visualizer = holoscan.operators.HolovizOp(
            self,
            name="holoviz",
            fullscreen=self._fullscreen,
            headless=self._headless,
            framebuffer_srgb=True,
            tensors=tensors,
            width=self._window_width,
            height=self._window_height,
        )
        
        self._counts = []
        self._oks = []
        csi_to_bayer_pools = []
        csi_to_bayer_operators = []
        receiver_operators = []
        image_processors = []
        bayer_pools = []
        demosaics = []
        timestamp_printers = []
        for index in range(len(self._positions)):
            pos = self._positions[index]

            if self._frame_limit:
                self._counts.append(
                    holoscan.conditions.CountCondition(
                        self,
                        name=f"count_{pos}",
                        count=self._frame_limit,
                    )
                )
                condition = self._counts[index]
            else:
                self._oks.append(
                    holoscan.conditions.BooleanCondition(
                        self, 
                        name=f"ok_{pos}",
                        enable_tick=True
                    )
                )
                condition = self._oks[index]
     
            self._cameras[index].set_mode(self._camera_mode)

            csi_to_bayer_pools.append(
                holoscan.resources.BlockMemoryPool(
                    self,
                    name=f"pool_{pos}",
                    # storage_type of 1 is device memory
                    storage_type=1,
                    block_size=self._cameras[index]._width 
                    * ctypes.sizeof(ctypes.c_uint16) 
                    * self._cameras[index]._height,
                    num_blocks=3,
                )
            )

            csi_to_bayer_operators.append(
                hololink_module.operators.CsiToBayerOp(
                    self,
                    name=f"csi_to_bayer_{pos}",
                    allocator=csi_to_bayer_pools[index],
                    cuda_device_ordinal=self._cuda_device_ordinal,
                    out_tensor_name=f"{pos}",
                )
            )
            self._cameras[index].configure_converter(csi_to_bayer_operators[index])

            frame_size = csi_to_bayer_operators[index].get_csi_length()
            frame_context = self._cuda_context

            receiver_operators.append(
                hololink_module.operators.LinuxReceiverOperator(
                    self,
                    condition,
                    name=f"receiver_{pos}",
                    frame_size=frame_size,
                    frame_context=frame_context,
                    hololink_channel=self._hololink_channels[index],
                    device=self._cameras[index],
                )
            )

            bayer_format = self._cameras[index].bayer_format()
            pixel_format = self._cameras[index].pixel_format()

            image_processors.append(
                hololink_module.operators.ImageProcessorOp(
                    self,
                    name=f"image_processor_{pos}",
                    optical_black=0,
                    bayer_format=bayer_format.value,
                    pixel_format=pixel_format.value,
                )
            )

            rgba_components_per_pixel = 4
            bayer_pools.append(
                holoscan.resources.BlockMemoryPool(
                    self,
                    name=f"pool_{pos}",
                    # storage_type of 1 is device memory
                    storage_type=1,
                    block_size=self._cameras[index]._width
                    * rgba_components_per_pixel
                    * ctypes.sizeof(ctypes.c_uint16)
                    * self._cameras[index]._height,
                    num_blocks=3,
                )
            )

            demosaics.append( 
                holoscan.operators.BayerDemosaicOp(
                    self,
                    name=f"demosaic_{pos}",
                    pool=bayer_pools[index],
                    generate_alpha=True,
                    alpha_value=65535,
                    bayer_grid_pos=bayer_format.value,
                    interpolation_mode=0,
                    in_tensor_name=f"{pos}",
                    out_tensor_name=f"{pos}",
                )
            )
        
            if self._print_time:
                timestamp_printers.append(
                    TimestampPrinterOp(
                        self, 
                        name=f"timestamp_printer_{pos}", 
                        camera_name=f"{pos}"
                    )
                )
                self.add_flow(receiver_operators[index], timestamp_printers[index], {("output", "input")})
                self.add_flow(timestamp_printers[index], csi_to_bayer_operators[index], {("output", "input")})
            else:
                self.add_flow(receiver_operators[index], csi_to_bayer_operators[index], {("output", "input")})

            self.add_flow(csi_to_bayer_operators[index], image_processors[index], {("output", "input")})
            self.add_flow(image_processors[index], demosaics[index], {("output", "receiver")})
            self.add_flow(demosaics[index], visualizer, {("transmitter", "receivers")})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--camera-mode",
        type=int,
        default=hololink_module.sensors.SG10A_AGON_G2M_Ax.sg2_ar0234c_gmsl_mode.Sensor_Mode.sensor_mode_1920x1200_raw12_4lane_30fps_linear.value,
        help="SG2-AR0234C-GMSL2 mode",
    )
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument(
        "--fullscreen", action="store_true", help="Run in fullscreen mode"
    )
    parser.add_argument(
        "--frame-limit",
        type=int,
        default=None,
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
        default=2,
        help="Logging level to display",
    )
    parser.add_argument(
        "--window_width",
        type=int, 
        default=1920,
        help="Set the width of the displayed window", 
    )
    parser.add_argument(
        "--window_height", 
        type=int, 
        default=1080,  
        help="Set the height of the displayed window",
    )
    parser.add_argument(
        "--expander-configuration",
        type=int,
        default=0,
        choices=(0, 1),
        help="I2C Expander configuration",
    )
    parser.add_argument(
        "--camera-positions",
        type=str,
        default="front,back",
        help="Comma-separated list of camera positions to enable (e.g., 'front', 'back', 'left', 'right', 'left,front')",
    )
    parser.add_argument(
        "--trigger",
        action="store_true",
        help="Run in trigger mode",
    )
    parser.add_argument(
        "--frequency",
        type=int,
        default=30,
        help="VSYNC frequency in Hz (10, 30, 60, 90, 120). Default is 30Hz",
    )
    parser.add_argument(
        "--print-time",
        action="store_true",
        help="Print timestamp information for received frames",
    )

    pos_to_cam_id = {
        "front": 0,
        "back": 1,
        "left": 2,
        "right": 3,
    }

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
    # Get a handle to the Hololink device & camera
    channel_metadata = hololink_module.Enumerator.find_channel(channel_ip=args.hololink)
    logging.info(f"{channel_metadata=}")
    
    positions = [pos.strip() for pos in args.camera_positions.split(",") if pos.strip()]
    logging.info(f"Enabling cameras at positions: {positions}")

    hololink_channels = []
    for pos in positions:
        if pos not in ["front", "back", "left", "right"]:
            raise ValueError(f"Unknown camera position: {pos}")

        cam_id = pos_to_cam_id[pos]
        logging.info(f"camera position at cam_id {cam_id}: {pos}")
        metadata = hololink_module.Metadata(channel_metadata)
        hololink_module.DataChannel.use_sensor(metadata, cam_id)
        channel = hololink_module.DataChannel(metadata)
        hololink_channels.append(channel)

    hololink = hololink_channels[0].hololink()
    for channel in hololink_channels[1:]:
        assert hololink is channel.hololink()

    vsync = hololink_module.Synchronizer.null_synchronizer()
    if args.trigger:
        vsync = hololink.ptp_pps_output(args.frequency)

    cameras = []
    for index in range(len(positions)):
        pos = positions[index]
        if pos in ["front", "back"]:
            camera = hololink_module.sensors.SG10A_AGON_G2M_Ax.sg2_ar0234c_gmsl.Ar0234Cam(
                channel, expander_configuration=0, position=pos, vsync=vsync,
            )
        else:
            camera = hololink_module.sensors.SG10A_AGON_G2M_Ax.sg2_ar0234c_gmsl.Ar0234Cam(
                channel, expander_configuration=1, position=pos, vsync=vsync,
            )
        cameras.append(camera)

    camera_mode = hololink_module.sensors.SG10A_AGON_G2M_Ax.sg2_ar0234c_gmsl_mode.Sensor_Mode(
        args.camera_mode
    )

    # Set up the application
    application = HoloscanApplication(
        args.headless,
        args.fullscreen,
        cu_context,
        cu_device_ordinal,
        positions,
        hololink_channels,
        cameras,
        camera_mode,
        args.frame_limit,
        args.window_height,
        args.window_width,
        args.print_time,
    )
    application.config(args.configuration)

    # Run it.
    hololink.start()
    hololink.reset()

    # power control
    gpio = hololink.get_gpio(channel_metadata)
    gpio.set_direction(0, gpio.OUT)
    gpio.set_direction(1, gpio.OUT)
    gpio.set_direction(18, gpio.OUT)
    gpio.set_direction(25, gpio.OUT)
    gpio.set_value(0, gpio.LOW)    # MAX9296 (U3) PWDNB
    gpio.set_value(1, gpio.LOW)    # MAX9296 (U4) PWDNB
    gpio.set_value(18, gpio.LOW)    # POC Power
    gpio.set_value(25, gpio.LOW)    # POC Power
    time.sleep(0.5)
    gpio.set_value(0, gpio.HIGH)    # MAX9296 (U3) PWDNB set High
    gpio.set_value(1, gpio.HIGH)    # MAX9296 (U4) PWDNB set High
    gpio.set_value(18, gpio.HIGH)    # POC Power Enable
    gpio.set_value(25, gpio.HIGH)    # POC Power Enable
    time.sleep(0.5)

    for index in range(len(positions)):
        cameras[index].setup_clock()
        cameras[index].configure(camera_mode)

    application.run()

    hololink.stop()

    (cu_result,) = cuda.cuDevicePrimaryCtxRelease(cu_device)
    assert cu_result == cuda.CUresult.CUDA_SUCCESS

if __name__ == "__main__":
    main()
