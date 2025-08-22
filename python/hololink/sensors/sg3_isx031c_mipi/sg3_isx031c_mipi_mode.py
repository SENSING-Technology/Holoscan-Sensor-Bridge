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
SENSOR_I2C_ADDRESS = 0x1a

# Register addresses for camera properties. They only accept 8bits of value.

sensor_start = [
    (SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS_START),
]

sensor_stop = [
    (SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS),
]

sensor_mode_1920x1536_30fps_yuv = [
    (SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS),
]

class Sensor_Mode(Enum):
    SENSOR_MODE_1920X1536_30FPS_YUV = 0
    Unknown = 1

frame_format = namedtuple(
    "FrameFormat", ["width", "height", "framerate", "pixel_format"]
)

sensor_frame_format = {
    Sensor_Mode.SENSOR_MODE_1920X1536_30FPS_YUV.value: frame_format(1920, 1536, 30, hololink.sensors.csi.PixelFormat.RAW_8),
}
