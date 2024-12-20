#!/usr/bin/env python3
#
# Copyright (c) 2018 Raptor Engineering, LLC
# Released under the terms of the AGPL v3

import sys
import os
import binascii

eeprom_bus = int(sys.argv[1])
if sys.argv[2].startswith("0x") or sys.argv[2].startswith("0X"):
    eeprom_address = int(sys.argv[2][2:], 16)
else:
    eeprom_address = int(sys.argv[2])
filename = sys.argv[3]

mod_ret = os.system("modprobe at24")
exit_code = os.WEXITSTATUS(mod_ret)
if exit_code != 0:
    print("[ERROR] at24 driver load failed!")
    sys.exit(1)

try:
    with open("/sys/class/i2c-dev/i2c-" + str(eeprom_bus) + "/device/" + str(eeprom_bus) + "-" + format(eeprom_address, '04x') + "/eeprom", 'rb') as f:
        origdata = f.read()
except:
    print("[ERROR] VPD not found on specified I2C bus!")
    sys.exit(1)

original_data = binascii.hexlify(origdata)
vpd_length = len(original_data)

if vpd_length != 131072:
    print("[ERROR] Invalid VPD length.  Aborting!")
    sys.exit(1)

with open(filename, 'wb') as f:
    f.write(origdata)
