#!/usr/bin/env python3
#
# Copyright (c) 2018 Raptor Engineering, LLC
# Released under the terms of the AGPL v3

import sys
import os
import glob

i2cdir = "/sys/class/i2c-dev/"
eeprom_address = 0x50

mod_ret = os.system("modprobe i2c_dev")
exit_code = os.WEXITSTATUS(mod_ret)
if exit_code != 0:
    print("[ERROR] I2C driver load failed!")
    sys.exit(1)

i2cbusses = glob.glob(i2cdir + "i2c-*")
busnumlist = []
for b in i2cbusses:
    bus = b.replace(i2cdir + "i2c-", "")
    busnumlist.append(int(bus))

busnumlist.sort()

mod_ret = os.system("modprobe at24")
exit_code = os.WEXITSTATUS(mod_ret)
if exit_code != 0:
    print("[ERROR] at24 driver load failed!")
    sys.exit(1)

print("The following I2C busses are available on this system:")
for b in busnumlist:
    sys.stdout.write("\tBus " + str(b))
    mvpd_found = False
    try:
        with open("/sys/class/i2c-dev/i2c-" + str(b) + "/device/" + str(b) + "-" + format(eeprom_address, '04x') + "/eeprom", 'rb') as f:
            f.seek(0, os.SEEK_END)
            if f.tell() == 65536:
                mvpd_found = True
                print(" (MVPD candidate found on bus)")
    except:
        pass

    if not mvpd_found:
        print("")
