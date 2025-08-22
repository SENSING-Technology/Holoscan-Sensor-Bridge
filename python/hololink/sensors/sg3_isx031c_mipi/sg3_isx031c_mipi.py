"""
SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import time
from collections import OrderedDict

import hololink as hololink_module

from . import li_i2c_expander, sg3_isx031c_mipi_mode

# Camera info
DRIVER_NAME = "SG3_ISX031C_MIPI"
VERSION = 1.0

class Isx031Cam:
    def __init__(
        self,
        hololink_channel,
        i2c_bus=hololink_module.CAM_I2C_BUS,
        expander_configuration=0,
    ):
        self._hololink_channel = hololink_channel
        self._hololink = hololink_channel.hololink()
        self._i2c_bus = i2c_bus
        self._i2c = self._hololink.get_i2c(i2c_bus)
        self._mode = sg3_isx031c_mipi_mode.Sensor_Mode.Unknown
        # Configure i2c expander
        self._i2c_expander = li_i2c_expander.LII2CExpander(self._hololink, i2c_bus)
        self._instance = expander_configuration
        if expander_configuration == 1:
            self._i2c_expander_configuration = (
                li_i2c_expander.I2C_Expander_Output_EN.OUTPUT_2
            )
        else:
            self._i2c_expander_configuration = (
                li_i2c_expander.I2C_Expander_Output_EN.OUTPUT_1
            )

    def setup_clock(self):
        # set the clock driver.
        logging.debug("setup_clock")
        self._hololink.setup_clock(
            hololink_module.renesas_bajoran_lite_ts1.device_configuration()
        )

    def configure(self, sensor_mode_set):
        # Make sure this is a version we know about.
        version = self.get_version()
        logging.info("version=%s" % (version,))
        assert version == VERSION

        # configure the camera based on the mode
        self.configure_camera(sensor_mode_set)

    def start(self):
        """Start Streaming"""
        self._running = True
        #
        # Setting these register is time-consuming.
        for i2c_addr, reg, val in sg3_isx031c_mipi_mode.sensor_start:
            if i2c_addr == sg3_isx031c_mipi_mode.SENSOR_TABLE_WAIT_MS:
                time.sleep(val / 1000)  # the val is in ms
            else:
                self.set_register(i2c_addr, reg, val)

    def stop(self):
        """Stop Streaming"""
        for i2c_addr, reg, val in sg3_isx031c_mipi_mode.sensor_stop:
            if i2c_addr == sg3_isx031c_mipi_mode.SENSOR_TABLE_WAIT_MS:
                time.sleep(val / 1000)  # the val is in ms
            else:
                self.set_register(i2c_addr, reg, val)
        # Let the egress buffer drain.
        time.sleep(0.1)
        self._running = False

    def get_version(self):
        # TODO: get the version or the name of the sensor from the sensor
        return VERSION

    def get_register(self, i2c_address, register):
        logging.debug("get_register(i2c address=0x%02X, register=0x%04X)" % (i2c_address, register))
        self._i2c_expander.configure(self._i2c_expander_configuration.value)
        write_bytes = bytearray(100)
        serializer = hololink_module.Serializer(write_bytes)
        serializer.append_uint16_be(register)
        read_byte_count = 1
        reply = self._i2c.i2c_transaction(
            i2c_address, write_bytes[: serializer.length()], read_byte_count
        )
        deserializer = hololink_module.Deserializer(reply)
        r = deserializer.next_uint8()
        logging.debug(
            "get_register(i2c address=0x%02X, register=0x%04X=0x%02X" % (i2c_address, register, r)
        )
        return r

    def set_register(self, i2c_address, register, value, timeout=None):
        logging.debug(
            "set_register(i2c address=0x%02X, register=0x%04X, value=0x%02X)"
            % (i2c_address, register, value)
        )
        self._i2c_expander.configure(self._i2c_expander_configuration.value)
        write_bytes = bytearray(100)
        serializer = hololink_module.Serializer(write_bytes)
        serializer.append_uint16_be(register)
        serializer.append_uint8(value)
        read_byte_count = 0
        self._i2c.i2c_transaction(
            i2c_address,
            write_bytes[: serializer.length()],
            read_byte_count,
            timeout=timeout,
        )

    def configure_camera(self, sensor_mode_set):
        self.set_mode(sensor_mode_set)

        sensor_mode_list = []

        if sensor_mode_set.value == sg3_isx031c_mipi_mode.Sensor_Mode.SENSOR_MODE_1920X1536_30FPS_YUV.value:
            sensor_mode_list = sg3_isx031c_mipi_mode.sensor_mode_1920x1536_30fps_yuv
        else:
            logging.error(f"{sensor_mode_set} mode is not present.")

        for i2c_addr, reg, val in sensor_mode_list:
            if i2c_addr == sg3_isx031c_mipi_mode.SENSOR_TABLE_WAIT_MS:
                time.sleep(val / 1000)  # the val is in ms
            else:
                self.set_register(i2c_addr, reg, val)

    def set_mode(self, sensor_mode_set):
        if sensor_mode_set.value < len(sg3_isx031c_mipi_mode.Sensor_Mode):
            self._mode = sensor_mode_set
            mode = sg3_isx031c_mipi_mode.sensor_frame_format[self._mode.value]
            self._height = mode.height
            self._width = mode.width
            self._pixel_format = mode.pixel_format
        else:
            logging.error("Incorrect mode for SENSOR")
            self._mode = -1

    def configure_converter(self, converter):
        # where do we find the first received byte?
        start_byte = converter.receiver_start_byte()
        transmitted_line_bytes = converter.transmitted_line_bytes(
            self._pixel_format, self._width
        )
        received_line_bytes = converter.received_line_bytes(transmitted_line_bytes)
        # We get 1 lines of metadata preceding the image data.
        start_byte += received_line_bytes * 1
        if self._pixel_format == hololink_module.sensors.csi.PixelFormat.YUV422_YUYV:

            start_byte += 0
        else:
            raise Exception(f"Incorrect pixel format={self._pixel_format} for ISX031.")
        converter.configure(
            start_byte,
            received_line_bytes,
            self._width,
            self._height,
            self._pixel_format,
        )

    def pixel_format(self):
        return self._pixel_format

    def bayer_format(self):
        return None
