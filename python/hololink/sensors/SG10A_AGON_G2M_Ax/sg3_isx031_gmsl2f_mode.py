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
SENSOR_WAIT_MS = 100

# I2C address
DSER_I2C_ADDRESS = 0x48

SER_DEF_I2C_ADDRESS = 0x40
SER_0_I2C_ADDRESS = 0x41
SER_1_I2C_ADDRESS = 0x42

SENSOR_DEF_I2C_ADDRESS = 0x36
SENSOR_0_I2C_ADDRESS = 0x11
SENSOR_1_I2C_ADDRESS = 0x12

# Exposure

sensor_start = [
    ( SER_DEF_I2C_ADDRESS, 0x0002, 0x43 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
]

sensor_stop = [
    ( SER_DEF_I2C_ADDRESS, 0x0002, 0x03 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
]

serdes_config_front = [
    ( DSER_I2C_ADDRESS, 0x0313, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0001, 0x01 ),

    ( DSER_I2C_ADDRESS, 0x0010, 0x21 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
    ( SER_DEF_I2C_ADDRESS, 0x0000, SER_0_I2C_ADDRESS*2 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),

    ( SER_0_I2C_ADDRESS, 0x0330, 0x00 ),
    ( SER_0_I2C_ADDRESS, 0x0383, 0x00 ),
    ( SER_0_I2C_ADDRESS, 0x0331, 0x30 ),
    ( SER_0_I2C_ADDRESS, 0x0332, 0xe0 ),
    ( SER_0_I2C_ADDRESS, 0x0333, 0x04 ),
    ( SER_0_I2C_ADDRESS, 0x0334, 0x00 ),
    ( SER_0_I2C_ADDRESS, 0x0335, 0x00 ),

    ( SER_0_I2C_ADDRESS, 0x0308, 0x64 ),
    ( SER_0_I2C_ADDRESS, 0x0311, 0x40 ),
    ( SER_0_I2C_ADDRESS, 0x0318, 0x5e ),
    ( SER_0_I2C_ADDRESS, 0x0315, 0x80 ),
    ( SER_0_I2C_ADDRESS, 0x030d, 0x01 ),
    ( SER_0_I2C_ADDRESS, 0x005B, 0x00 ), 

    # sensor i2c address
    ( SER_0_I2C_ADDRESS, 0x0042, SENSOR_0_I2C_ADDRESS*2 ),
    ( SER_0_I2C_ADDRESS, 0x0043, SENSOR_DEF_I2C_ADDRESS*2 ),
    #sync
    ( SER_0_I2C_ADDRESS, 0x02D3, 0x00 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
    ( SER_0_I2C_ADDRESS, 0x02D3, 0x10 ),

    ( DSER_I2C_ADDRESS, 0x0050, 0x00 ),

    ( DSER_I2C_ADDRESS, 0x040B, 0x07 ),
    ( DSER_I2C_ADDRESS, 0x040C, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x040D, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x040E, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x040F, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0410, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0411, 0x01 ),
    ( DSER_I2C_ADDRESS, 0x0412, 0x01 ),
    ( DSER_I2C_ADDRESS, 0x042D, 0x15 ),

    ( DSER_I2C_ADDRESS, 0x044B, 0x07 ),
    ( DSER_I2C_ADDRESS, 0x044C, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x044D, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x044E, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x044F, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0450, 0x40 ),
    ( DSER_I2C_ADDRESS, 0x0451, 0x01 ),
    ( DSER_I2C_ADDRESS, 0x0452, 0x41 ),
    ( DSER_I2C_ADDRESS, 0x046D, 0x15 ),

    ( DSER_I2C_ADDRESS, 0x0330, 0x04 ),
    ( DSER_I2C_ADDRESS, 0x0333, 0x4E ),
    ( DSER_I2C_ADDRESS, 0x0334, 0xE4 ),
    ( DSER_I2C_ADDRESS, 0x044A, 0xD0 ),
    ( DSER_I2C_ADDRESS, 0x0335, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x1D00, 0xF4 ),

    ( DSER_I2C_ADDRESS, 0x0320, 0x2C ),
    ( DSER_I2C_ADDRESS, 0x1D00, 0xF5 ),
    ( DSER_I2C_ADDRESS, 0x0332, 0x30 ),
    ( DSER_I2C_ADDRESS, 0x0313, 0x02 ),
    #sync
    ( DSER_I2C_ADDRESS, 0x0003, 0x40 ),
    ( DSER_I2C_ADDRESS, 0x02BF, 0x83 ),
    ( DSER_I2C_ADDRESS, 0x02C0, 0xA7 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
]

serdes_config_back = [
    ( DSER_I2C_ADDRESS, 0x0313, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0001, 0x01 ),

    ( DSER_I2C_ADDRESS, 0x0010, 0x22 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
    ( SER_DEF_I2C_ADDRESS, 0x0000, SER_1_I2C_ADDRESS*2 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
    
    ( SER_1_I2C_ADDRESS, 0x0330, 0x00 ),
    ( SER_1_I2C_ADDRESS, 0x0383, 0x00 ),
    ( SER_1_I2C_ADDRESS, 0x0331, 0x30 ),
    ( SER_1_I2C_ADDRESS, 0x0332, 0xe0 ),
    ( SER_1_I2C_ADDRESS, 0x0333, 0x04 ),
    ( SER_1_I2C_ADDRESS, 0x0334, 0x00 ),
    ( SER_1_I2C_ADDRESS, 0x0335, 0x00 ),

    ( SER_1_I2C_ADDRESS, 0x0308, 0x64 ),
    ( SER_1_I2C_ADDRESS, 0x0311, 0x40 ),
    ( SER_1_I2C_ADDRESS, 0x0318, 0x5e ),
    ( SER_1_I2C_ADDRESS, 0x0315, 0x80 ),
    ( SER_1_I2C_ADDRESS, 0x030d, 0x01 ),
    ( SER_1_I2C_ADDRESS, 0x005B, 0x01 ), 

    # sensor i2c address
    ( SER_1_I2C_ADDRESS, 0x0042, SENSOR_1_I2C_ADDRESS*2 ),
    ( SER_1_I2C_ADDRESS, 0x0043, SENSOR_DEF_I2C_ADDRESS*2 ),
    #sync
    ( SER_1_I2C_ADDRESS, 0x02D3, 0x00 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
    ( SER_1_I2C_ADDRESS, 0x02D3, 0x10 ),

    ( DSER_I2C_ADDRESS, 0x0050, 0x01 ),

    ( DSER_I2C_ADDRESS, 0x040B, 0x07 ),
    ( DSER_I2C_ADDRESS, 0x040C, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x040D, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x040E, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x040F, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0410, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0411, 0x01 ),
    ( DSER_I2C_ADDRESS, 0x0412, 0x01 ),
    ( DSER_I2C_ADDRESS, 0x042D, 0x15 ),

    ( DSER_I2C_ADDRESS, 0x044B, 0x07 ),
    ( DSER_I2C_ADDRESS, 0x044C, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x044D, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x044E, 0x1E ),
    ( DSER_I2C_ADDRESS, 0x044F, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x0450, 0x40 ),
    ( DSER_I2C_ADDRESS, 0x0451, 0x01 ),
    ( DSER_I2C_ADDRESS, 0x0452, 0x41 ),
    ( DSER_I2C_ADDRESS, 0x046D, 0x15 ),

    ( DSER_I2C_ADDRESS, 0x0330, 0x04 ),
    ( DSER_I2C_ADDRESS, 0x0333, 0x4E ),
    ( DSER_I2C_ADDRESS, 0x0334, 0xE4 ),
    ( DSER_I2C_ADDRESS, 0x044A, 0xD0 ),
    ( DSER_I2C_ADDRESS, 0x0335, 0x00 ),
    ( DSER_I2C_ADDRESS, 0x1D00, 0xF4 ),

    ( DSER_I2C_ADDRESS, 0x0320, 0x2C ),
    ( DSER_I2C_ADDRESS, 0x1D00, 0xF5 ),
    ( DSER_I2C_ADDRESS, 0x0332, 0x30 ),
    ( DSER_I2C_ADDRESS, 0x0313, 0x02 ),
     #sync
    ( DSER_I2C_ADDRESS, 0x0003, 0x40 ),
    ( DSER_I2C_ADDRESS, 0x02BF, 0x83 ),
    ( DSER_I2C_ADDRESS, 0x02C0, 0xA7 ),
    ( SENSOR_TABLE_WAIT_MS, 0x0000, SENSOR_WAIT_MS ),
]

#master
sensor_mode_1920x1536_30fps_yuv = [
]

sensor_enable_sync_front = [
    ( SER_0_I2C_ADDRESS, 0x02D3, 0x04 ),
    ( SER_0_I2C_ADDRESS, 0x02D5, 0x07 ),
]

sensor_enable_sync_back = [
    ( SER_1_I2C_ADDRESS, 0x02D3, 0x04 ),
    ( SER_1_I2C_ADDRESS, 0x02D5, 0x07 ),
]

class Sensor_Mode(Enum):
    sensor_mode_1920x1536_30fps_yuv = 0
    Unknown = 1

frame_format = namedtuple(
    "FrameFormat", ["width", "height", "framerate", "pixel_format"]
)

sensor_frame_format = {
    Sensor_Mode.sensor_mode_1920x1536_30fps_yuv.value: frame_format(1920, 1536, 30, hololink.sensors.csi.PixelFormat.RAW_8),
}

