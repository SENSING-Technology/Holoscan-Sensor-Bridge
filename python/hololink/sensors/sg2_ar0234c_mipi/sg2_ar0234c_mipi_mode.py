"""
SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from collections import namedtuple
from enum import Enum

import hololink

# values are on hex number system to be consistent with rest of the list
SENSOR_TABLE_WAIT_MS = "sensor-table-wait-ms"
SENSOR_WAIT_MS = 0x01
SENSOR_WAIT_MS_START = 0xC8

# I2C address
SENSOR_I2C_ADDRESS = 0x18

# Register addresses for camera properties. They only accept 8bits of value.

# Exposure
REG_EXP_SHS1_ADDR_MSB = 0xABEE
REG_EXP_SHS1_ADDR_MID = 0xABED
REG_EXP_SHS1_ADDR_LSB = 0xABEC
REG_EXP_SHS2_ADDR_MSB = 0x0012
REG_EXP_SHS2_ADDR_MID = 0x0011
REG_EXP_SHS2_ADDR_LSB = 0x0010

# Analog Gain
REG_AG_MSB = 0x3060
REG_AG_LSB = 0x3061

sensor_start = [
    ( SENSOR_I2C_ADDRESS, 0x301A, 0x20 ),
    ( SENSOR_I2C_ADDRESS, 0x301B, 0x5C ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS_START ),
]

sensor_stop = [
    ( SENSOR_I2C_ADDRESS, 0x301A, 0x20 ),
    ( SENSOR_I2C_ADDRESS, 0x301B, 0x58 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
]

sensor_mode_1920x1200_raw12_4lane_30fps_linear = [
    ( SENSOR_I2C_ADDRESS, 0x302A, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x302B, 0x06 ),
    ( SENSOR_I2C_ADDRESS, 0x302C, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x302D, 0x01 ),
    ( SENSOR_I2C_ADDRESS, 0x302E, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x302F, 0x04 ),
    ( SENSOR_I2C_ADDRESS, 0x3030, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3031, 0x5A ),
    ( SENSOR_I2C_ADDRESS, 0x3036, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3037, 0x0C ),
    ( SENSOR_I2C_ADDRESS, 0x3038, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3039, 0x01 ),
    ( SENSOR_I2C_ADDRESS, 0x31B0, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x31B1, 0x67 ),
    ( SENSOR_I2C_ADDRESS, 0x31B2, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x31B3, 0x34 ),
    ( SENSOR_I2C_ADDRESS, 0x31B4, 0x22 ),
    ( SENSOR_I2C_ADDRESS, 0x31B5, 0x48 ),
    ( SENSOR_I2C_ADDRESS, 0x31B6, 0x32 ),
    ( SENSOR_I2C_ADDRESS, 0x31B7, 0x5A ),
    ( SENSOR_I2C_ADDRESS, 0x31B8, 0x90 ),
    ( SENSOR_I2C_ADDRESS, 0x31B9, 0x4A ),
    ( SENSOR_I2C_ADDRESS, 0x31BA, 0x02 ),
    ( SENSOR_I2C_ADDRESS, 0x31BB, 0x8B ),
    ( SENSOR_I2C_ADDRESS, 0x31BC, 0x8E ),
    ( SENSOR_I2C_ADDRESS, 0x31BD, 0x09 ),
    ( SENSOR_I2C_ADDRESS, 0x3354, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3355, 0x2C ),
    ( SENSOR_I2C_ADDRESS, 0x301A, 0x20 ),
    ( SENSOR_I2C_ADDRESS, 0x301B, 0x58 ),
    ( SENSOR_I2C_ADDRESS, 0x31AE, 0x02 ),
    ( SENSOR_I2C_ADDRESS, 0x31AF, 0x04 ),
    ( SENSOR_I2C_ADDRESS, 0x3002, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3003, 0x08 ),
    ( SENSOR_I2C_ADDRESS, 0x3004, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3005, 0x08 ),
    ( SENSOR_I2C_ADDRESS, 0x3006, 0x04 ),
    ( SENSOR_I2C_ADDRESS, 0x3007, 0xB7 ),
    ( SENSOR_I2C_ADDRESS, 0x3008, 0x07 ),
    ( SENSOR_I2C_ADDRESS, 0x3009, 0x87 ),
    ( SENSOR_I2C_ADDRESS, 0x300A, 0x13 ),
    ( SENSOR_I2C_ADDRESS, 0x300B, 0x06 ),
    ( SENSOR_I2C_ADDRESS, 0x300C, 0x02 ),
    ( SENSOR_I2C_ADDRESS, 0x300D, 0x68 ),
    ( SENSOR_I2C_ADDRESS, 0x3012, 0x13 ),
    ( SENSOR_I2C_ADDRESS, 0x3013, 0x05 ),
    ( SENSOR_I2C_ADDRESS, 0x31AC, 0x0C ),
    ( SENSOR_I2C_ADDRESS, 0x31AD, 0x0C ),
    ( SENSOR_I2C_ADDRESS, 0x306E, 0x90 ),
    ( SENSOR_I2C_ADDRESS, 0x306F, 0x10 ),
    ( SENSOR_I2C_ADDRESS, 0x30A2, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x30A3, 0x01 ),
    ( SENSOR_I2C_ADDRESS, 0x30A6, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x30A7, 0x01 ),
    ( SENSOR_I2C_ADDRESS, 0x3082, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3083, 0x03 ),
    ( SENSOR_I2C_ADDRESS, 0x3040, 0xC0 ),
    ( SENSOR_I2C_ADDRESS, 0x3041, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x3071, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x31D0, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x31D1, 0x00 ),
    ( SENSOR_I2C_ADDRESS, 0x301A, 0x20 ),
    ( SENSOR_I2C_ADDRESS, 0x301B, 0x5C ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
]

class Sensor_Mode(Enum):
    sensor_mode_1920x1200_raw12_4lane_30fps_linear = 0
    Unknown = 1


frame_format = namedtuple(
    "FrameFormat", ["width", "height", "framerate", "pixel_format"]
)

sensor_frame_format = {
    Sensor_Mode.sensor_mode_1920x1200_raw12_4lane_30fps_linear.value: frame_format(1920, 1200, 30, hololink.sensors.csi.PixelFormat.RAW_12),
}
