#!/usr/bin/env python2
#
# Copyright (c) 2018 Raptor Engineering, LLC
# Released under the terms of the AGPL v3
#
# NOTE:
# #V bucket layout documented in p9_pm_get_poundw_bucket.H,
# type vdmData_t

import sys
import binascii

def show_poundw_bucket_mode_data(mode_data, friendly_name):
    print "\t" + friendly_name + ":"
    sys.stdout.write("\t\t")
    count = 0
    for data in mode_data:
        sys.stdout.write(data + ", ")
        count = count + 1
        if (count > 20):
            print ""
            sys.stdout.write("\t\t")
            count = 0
    print ""

def parse_poundw_bucket(bucket_data):
    id = bucket_data[2:]
    data = map(''.join, zip(*[iter(bucket_data[2:])]*2))

    return id, data

def assemble_poundw_bucket(id, data):
    new_bucket_data = id + "".join(data)
    return new_bucket_data

source_bucket = int(sys.argv[1]) - 1
destination_bucket = int(sys.argv[2]) - 1
raw_data = sys.argv[3]

if (source_bucket < 0) or (source_bucket > 5):
    print "[ERROR] Invalid source bucket specified"
    sys.exit(1)

if (destination_bucket < 0) or (destination_bucket > 5):
    print "[ERROR] Invalid destination bucket specified"
    sys.exit(1)

if source_bucket == destination_bucket:
    print "[ERROR] Cannot copy to same destination bucket as origin bucket"
    sys.exit(1)

# #W buckets start at offset 4, and run for 60 bytes each
# 6 buckets are defined
bucket = ["", "", "", "", "", ""]
header = raw_data[:2]
version = header[:2]
bucket[0] = raw_data[2:124]
bucket[1] = raw_data[124:246]
bucket[2] = raw_data[246:368]
bucket[3] = raw_data[368:490]
bucket[4] = raw_data[490:612]
bucket[5] = raw_data[612:734]

print "#W data block update"
print "=========================================="
print "Header:\t\t" + header
print "Version:\t" + str(int(version, 16))
print ""
for index in range (0, 6):
    if bucket[index][2:].startswith("0000"):
        continue

    print "Bucket " + str(index + 1) + ":\t" + bucket[index]

    id, data = parse_poundw_bucket(bucket[index])
    show_poundw_bucket_mode_data(data, "VDM data")

    print ""

print "Copying and adjusting data from bucket " + str(source_bucket + 1) + " to bucket " + str(destination_bucket + 1)
if bucket[source_bucket][2:].startswith("0000"):
    print "[ERROR] Source bucket data not valid"
    sys.exit(1)

id, data = parse_poundw_bucket(bucket[source_bucket])
new_id = format(destination_bucket + 1, '02x')
bucket[destination_bucket] = assemble_poundw_bucket(new_id, data)

print "\tModified bucket:\t" + bucket[destination_bucket]
show_poundw_bucket_mode_data(data, "VDM data")

new_bucket_data = header + "".join(bucket)

search_binstring = binascii.unhexlify(raw_data)
replace_binstring = binascii.unhexlify(new_bucket_data)

with open("search.bin", 'wb') as f:
    f.write(search_binstring)
with open("replace.bin", 'wb') as f:
    f.write(replace_binstring)

print ""
