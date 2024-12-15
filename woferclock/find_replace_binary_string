#!/usr/bin/env python2
#
# Copyright (c) 2018 Raptor Engineering, LLC
# Released under the terms of the AGPL v3

import sys
import binascii

filename = sys.argv[1]
searchfile = sys.argv[2]
replacefile = sys.argv[3]

with open(filename, 'rb') as f:
    indata = f.read()
with open(searchfile, 'rb') as f:
    searchdata = f.read()
with open(replacefile, 'rb') as f:
    replacedata = f.read()

raw_data = binascii.hexlify(indata)
search = binascii.hexlify(searchdata)
replace = binascii.hexlify(replacedata)
raw_data = raw_data.replace(search, replace)
outdata = binascii.unhexlify(raw_data)

with open(filename, 'wb') as f:
    f.write(outdata)
