#!/usr/bin/env python3
#
# Copyright (c) 2018 Raptor Engineering, LLC
# Released under the terms of the AGPL v3

import sys
import os
import time
import binascii
import subprocess

eeprom_bus = int(sys.argv[1])
if sys.argv[2].startswith("0x") or sys.argv[2].startswith("0X"):
    eeprom_address = int(sys.argv[2][2:], 16)
else:
    eeprom_address = int(sys.argv[2])
filename = sys.argv[3]

with open(filename, 'rb') as f:
    indata = f.read()

raw_data = binascii.hexlify(indata)
vpd_length = len(raw_data)

if vpd_length != 131072:
    print("[ERROR] Invalid VPD length.  Aborting!")
    sys.exit(1)

mod_ret = os.system("modprobe at24")
exit_code = os.WEXITSTATUS(mod_ret)
if exit_code != 0:
    print("[ERROR] at24 driver load failed!")
    sys.exit(1)

with open("/sys/class/i2c-dev/i2c-" + str(eeprom_bus) + "/device/" + str(eeprom_bus) + "-" + format(eeprom_address, '04x') + "/eeprom", 'rb') as f:
    origdata = f.read()

original_data = binascii.hexlify(origdata)

mod_ret = os.system("rmmod at24")
exit_code = os.WEXITSTATUS(mod_ret)
if exit_code != 0:
    print("[ERROR] at24 driver unload failed!")
    sys.exit(1)

address = 0
for i in range(0, vpd_length, 2):
    if original_data[i:(i+2)] != raw_data[i:(i+2)]:
        address_high = hex((address & 65280) >> 8)
        address_low = hex(address & 255)
        command = "i2cset -y " + str(eeprom_bus) + " 0x" + format(eeprom_address, '02x') + " " +  address_high + " " + address_low + " 0x" + raw_data[i:(i+2)] + " i 2>/dev/null"
        try:
            subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True)
        except:
            # Retry, giving the SEEPROM some time to recover
            time.sleep(0.1)
            try:
                subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True)
            except:
                print("[ERROR] Write failed!")
                print("\tCommand was: " + command)
                sys.exit(1)
    address = address + 1
    sys.stdout.write(format(address, '05d') + " / " + format((vpd_length / 2), '05d') + "\r")
    sys.stdout.flush()

print("")

mod_ret = os.system("modprobe at24")
exit_code = os.WEXITSTATUS(mod_ret)
if exit_code != 0:
    print("[ERROR] at24 driver load failed!")
    sys.exit(1)

with open("/sys/class/i2c-dev/i2c-" + str(eeprom_bus) + "/device/" + str(eeprom_bus) + "-" + format(eeprom_address, '04x') + "/eeprom", 'rb') as f:
    readdata = f.read()

readback_data = binascii.hexlify(readdata)
if (readback_data != raw_data):
    print("[WARNING] Readback did NOT match provided file!  VPD in unknown state!")
    sys.exit(2)
else:
    print("Done!")
