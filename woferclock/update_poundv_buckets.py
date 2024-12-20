#!/usr/bin/env python3
#
# Copyright (c) 2018 Raptor Engineering, LLC
# Released under the terms of the AGPL v3
#
# NOTE:
# #V bucket layout documented in p9_pm_get_poundv_bucket.H,
# type voltageBucketData_t

import sys
import binascii

def show_poundv_bucket_mode_data(mode_data, friendly_name):
    print("\t" + friendly_name + ":")
    print("\t\tFrequency:\t" + mode_data[0] + " (" + str(int(mode_data[0], 16)) + " MHz)")
    print("\t\tVDD Nominal:\t" + mode_data[1] + " (" + str(int(mode_data[1], 16)) + " mV)")
    print("\t\tIDD Nominal:\t" + mode_data[2] + " (" + str(int(mode_data[2], 16)) + " mA)")
    print("\t\tVCS Nominal:\t" + mode_data[3] + " (" + str(int(mode_data[3], 16)) + " mV)")
    print("\t\tICS Nominal:\t" + mode_data[4] + " (" + str(int(mode_data[4], 16)) + " mA)")

def show_poundv_bucket_power_data(power_data, friendly_name):
    print("\t" + friendly_name + ":")
    print("\t\tPower 1:\t" + power_data[0] + " (" + str(int(power_data[0], 16)) + " W)")
    print("\t\tPower 2:\t" + power_data[1] + " (" + str(int(power_data[0], 16)) + " W)")

def parse_poundv_bucket(bucket_data):
    modes = list(map(''.join, list(zip(*[iter(bucket_data[2:])]*20))))
    id = bucket_data[:2]
    nominal = list(map(''.join, list(zip(*[iter(modes[0])]*4))))
    powersave = list(map(''.join, list(zip(*[iter(modes[1])]*4))))
    turbo = list(map(''.join, list(zip(*[iter(modes[2])]*4))))
    ultraturbo = list(map(''.join, list(zip(*[iter(modes[3])]*4))))
    powerbus = list(map(''.join, list(zip(*[iter(modes[4])]*4))))
    sortpower = list(map(''.join, list(zip(*[iter(modes[5])]*4))))

    return id, nominal, powersave, turbo, ultraturbo, powerbus, sortpower

def assemble_poundv_bucket(id, nominal, powersave, turbo, ultraturbo, powerbus, sortpower):
    modes_reassembled = ["", "", "", "", "", ""]
    modes_reassembled[0] = "".join(nominal)
    modes_reassembled[1] = "".join(powersave)
    modes_reassembled[2] = "".join(turbo)
    modes_reassembled[3] = "".join(ultraturbo)
    modes_reassembled[4] = "".join(powerbus)
    modes_reassembled[5] = "".join(sortpower)

    new_bucket_data = id + "".join(modes_reassembled)
    return new_bucket_data

source_bucket = int(sys.argv[1]) - 1
destination_bucket = int(sys.argv[2]) - 1
new_powerbus_mhz = int(sys.argv[3])
new_ultraturbo_mhz = int(sys.argv[4])
voltage_multiplier = float(sys.argv[5])
raw_data = sys.argv[6]

# Rated limit plus safety margin
#max_voltage = 1098

# Absolute maximum process limit
# Hardware damage WILL occur above this value!
max_voltage = 1150

if (source_bucket < 0) or (source_bucket > 5):
    print("[ERROR] Invalid source bucket specified")
    sys.exit(1)

if (destination_bucket < 0) or (destination_bucket > 5):
    print("[ERROR] Invalid destination bucket specified")
    sys.exit(1)

if source_bucket == destination_bucket:
    print("[ERROR] Cannot copy to same destination bucket as origin bucket")
    sys.exit(1)

# #V buckets start at offset 4, and run for 61 bytes each
# 6 buckets are defined
bucket = ["", "", "", "", "", ""]
header = raw_data[:8]
version = header[:2]
bucket[0] = raw_data[8:130]
bucket[1] = raw_data[130:252]
bucket[2] = raw_data[252:374]
bucket[3] = raw_data[374:496]
bucket[4] = raw_data[496:618]
bucket[5] = raw_data[618:740]

print("#V data block update")
print("==========================================")
print("Header:\t\t" + header)
print("Version:\t" + str(int(version, 16)))
print("")
for index in range (0, 5):
    if bucket[index][2:].startswith("0000"):
        continue

    if len(bucket[index][2:]) != 120:
        if destination_bucket == (index + 1):
            print("[ERROR] Source bucket invalid")
            sys.exit(1)
        print("Skipping invalid bucket " + str(index + 1))
        continue

    print("Bucket " + str(index + 1) + ":\t" + bucket[index])

    id, nominal, powersave, turbo, ultraturbo, powerbus, sortpower = parse_poundv_bucket(bucket[index])

    show_poundv_bucket_mode_data(powersave, "Powersave")
    show_poundv_bucket_mode_data(nominal, "Nominal")
    show_poundv_bucket_mode_data(turbo, "Turbo")
    show_poundv_bucket_mode_data(ultraturbo, "Ultra Turbo")
    show_poundv_bucket_mode_data(powerbus, "PowerBus")
    show_poundv_bucket_power_data(sortpower, "Sort Power")

    print("")

print("Copying and adjusting data from bucket " + str(source_bucket + 1) + " to bucket " + str(destination_bucket + 1))
if bucket[source_bucket][2:].startswith("0000"):
    print("[ERROR] Source bucket data not valid")
    sys.exit(1)

id, nominal, powersave, turbo, ultraturbo, powerbus, sortpower = parse_poundv_bucket(bucket[source_bucket])
new_id = format(destination_bucket + 1, '02x')
ultraturbo_ratio = float(new_ultraturbo_mhz) / int(ultraturbo[0], 16)
print("\tUltraturbo ratio:\t" + str(ultraturbo_ratio))
ultraturbo[0] = format(int(new_ultraturbo_mhz), '04x')
turbo[0] = format(int(int(turbo[0], 16) * ultraturbo_ratio), '04x')
nominal[0] = format(int(int(nominal[0], 16) * ultraturbo_ratio), '04x')
powersave[0] = format(int(int(powersave[0], 16) * ultraturbo_ratio), '04x')
powerbus[0] = format(new_powerbus_mhz, '04x')
new_voltage = voltage_multiplier * int(ultraturbo[1], 16)
if (new_voltage > max_voltage):
    new_voltage = max_voltage
ultraturbo[1] = format(int(new_voltage), '04x')
new_voltage = voltage_multiplier * int(turbo[1], 16)
if (new_voltage > max_voltage):
    new_voltage = max_voltage
turbo[1] = format(int(new_voltage), '04x')
new_voltage = voltage_multiplier * int(nominal[1], 16)
if (new_voltage > max_voltage):
    new_voltage = max_voltage
nominal[1] = format(int(new_voltage), '04x')
new_voltage = voltage_multiplier * int(powersave[1], 16)
if (new_voltage > max_voltage):
    new_voltage = max_voltage
powersave[1] = format(int(new_voltage), '04x')
new_voltage = voltage_multiplier * int(powerbus[1], 16)
if (new_voltage > max_voltage):
    new_voltage = max_voltage
powerbus[1] = format(int(new_voltage), '04x')
ultraturbo[2] = format(int(voltage_multiplier * int(ultraturbo[2], 16)), '04x')
turbo[2] = format(int(voltage_multiplier * int(turbo[2], 16)), '04x')
nominal[2] = format(int(voltage_multiplier * int(nominal[2], 16)), '04x')
powersave[2] = format(int(voltage_multiplier * int(powersave[2], 16)), '04x')
powerbus[2] = format(int(voltage_multiplier * int(powerbus[2], 16)), '04x')
bucket[destination_bucket] = assemble_poundv_bucket(new_id, nominal, powersave, turbo, ultraturbo, powerbus, sortpower)

print("\tModified bucket:\t" + bucket[destination_bucket])
show_poundv_bucket_mode_data(powersave, "Powersave")
show_poundv_bucket_mode_data(nominal, "Nominal")
show_poundv_bucket_mode_data(turbo, "Turbo")
show_poundv_bucket_mode_data(ultraturbo, "Ultra Turbo")
show_poundv_bucket_mode_data(powerbus, "PowerBus")
show_poundv_bucket_power_data(sortpower, "Sort Power")

new_bucket_data = header + "".join(bucket)

search_binstring = binascii.unhexlify(raw_data)
replace_binstring = binascii.unhexlify(new_bucket_data)

with open("search.bin", 'wb') as f:
    f.write(search_binstring)
with open("replace.bin", 'wb') as f:
    f.write(replace_binstring)

print("")
