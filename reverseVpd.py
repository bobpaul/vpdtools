#!/usr/bin/env python2
# Created 03/20/15 by Jason Albert
# Program to deconstruct a VPD image into xml template files

# IBM_PROLOG_BEGIN_TAG
# This is an automatically generated prolog.
#
# OpenPOWER HostBoot Project
#
# Contributors Listed Below - COPYRIGHT 2010,2014
# [+] International Business Machines Corp.
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
#
# IBM_PROLOG_END_TAG

############################################################
# Imports - Imports - Imports - Imports - Imports - Imports
############################################################
import os
# Get the path the script resides in
scriptPath = os.path.dirname(os.path.realpath(__file__))
import sys
sys.path.insert(0,scriptPath + "/pymod");
import argparse
import textwrap
import out
import xml.etree.ElementTree as ET
import struct
import re
import binascii
import string
import operator

def asciiAllowed(s):
    for c in s:
        if c not in string.printable:
            return False
    return True

############################################################
# Classes - Classes - Classes - Classes - Classes - Classes
############################################################
class RecordInfo:
    """Stores the info about each vpd record"""
    def __init__(self):
        # The name of the record
        self.recordName = None
        # The location of the Record Offset
        self.recordOffset = None
        # The location of the Record Length
        self.recordLength = None
        # The location of the ECC Offset
        self.eccOffset = None
        # The location of the ECC Length
        self.eccLength = None

############################################################
# Function - Functions - Functions - Functions - Functions
############################################################
# Function to write out the resultant tvpd xml file
def writeTvpd(manifest, outputFile):
    tree = ET.ElementTree(manifest)
    tree.write(outputFile, encoding="utf-8", xml_declaration=True)
    return None

############################################################
# Main - Main - Main - Main - Main - Main - Main - Main
############################################################
rc = 0

################################################
# Command line options
# Create the argparser object
# We disable auto help options here and add them manually below.  This is we can get all the optional args in 1 group
parser = argparse.ArgumentParser(description='Reverses a VPD image into XML template files', add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=textwrap.dedent('''\
                                 Examples:
                                   ./reverseVpd.py -v image.vpd -o /tmp
                                 '''))
# Create our group of required command line args
reqgroup = parser.add_argument_group('Required Arguments')
reqgroup.add_argument('-v', '--vpdfile', help='The valid vpd formatted input file', required=True)
reqgroup.add_argument('-o', '--outpath', help='The output path for the files created by the tool', required=True)
# Create our group of optional command line args
optgroup = parser.add_argument_group('Optional Arguments')
optgroup.add_argument('-h', '--help', action="help", help="Show this help message and exit")
optgroup.add_argument('-d', '--debug', help="Enables debug printing",action="store_true")
optgroup.add_argument('-r', '--create-records', help="Create tvpd files for each record in the vpd",action="store_true")

# We've got everything we want loaded up, now look for it
args = parser.parse_args()

# Get the manifest file and get this party started
clVpdFile = args.vpdfile

# Look for output path
clOutputPath = args.outpath
# Make sure the path exists, we aren't going to create it
if (os.path.exists(clOutputPath) != True):
    out.error("The given output path %s does not exist!" % clOutputPath)
    out.error("Please create the output directory and run again")
    exit(1)

# Debug printing
clDebug = args.debug

# Create separate tvpd files for each record
clCreateRecords = args.create_records

################################################
# Read in the VPD file and break it apart
out.setIndent(0)
out.msg("==== Stage 1: Parsing the VPD file")
out.setIndent(2)

# Create our output name from the input name
vpdName = os.path.splitext(os.path.basename(clVpdFile))[0]

# Open the vpdfile
vpdContents = open(clVpdFile, mode='rb').read()

# Jump right to where the VTOC should be and make sure it says VTOC
offset = 61
if (vpdContents[offset:(offset+4)].decode() != "VTOC"):
    out.error("Did not find VTOC at the expected offset!")
    exit(1)
offset+=4

# Skip the PT keyword and read the 1 byte length to loop over the VTOC contents and create our record list
offset+=2 # PT skip
tocLength = struct.unpack('<B', vpdContents[offset:(offset + 1)])[0]
offset+=1

# Keep a dictionary of the record names we come across
recordNames = dict()

# Loop through the toc and read out the record locations
tocOffset = 0
while (tocOffset < tocLength):
    # Get the record name
    recordName = vpdContents[(tocOffset + offset):(tocOffset + offset + 4)].decode()
    # Create the entry with the name
    recordNames[recordName] = RecordInfo()
    recordNames[recordName].recordName = recordName
    tocOffset+=4
    # Skip the record type
    tocOffset+=2
    # recordOffset
    recordNames[recordName].recordOffset = struct.unpack('<H', vpdContents[(tocOffset + offset):(tocOffset + offset + 2)])[0]
    tocOffset+=2
    # recordLength
    recordNames[recordName].recordLength = struct.unpack('<H', vpdContents[(tocOffset + offset):(tocOffset + offset + 2)])[0]
    tocOffset+=2
    # eccOffset
    recordNames[recordName].eccOffset = struct.unpack('<H', vpdContents[(tocOffset + offset):(tocOffset + offset + 2)])[0]
    tocOffset+=2
    # eccLength
    recordNames[recordName].eccLength = struct.unpack('<H', vpdContents[(tocOffset + offset):(tocOffset + offset + 2)])[0]
    tocOffset+=2

# We have all the record offsets in memory along with the entire VPD image.
# Go onto our next step and create XML in memory

################################################
# Create tvpd XML
out.setIndent(0)
out.msg("==== Stage 2: Creating tvpd XML")
out.setIndent(2)

# Create our top level level XML
vpd = ET.Element("vpd")

# Stick in our required tags
ET.SubElement(vpd, "name").text = vpdName
ET.SubElement(vpd, "size").text = "32 kB"
# VD is in a fixed location in VHDR, just rip it out instead of reading teh VPD to find it
ET.SubElement(vpd, "VD").text = ("%02X" % struct.unpack('<H', vpdContents[24:26])[0])

recordTvpd = dict()
# If we are going to be creating individual record vpd files
# Stash away the top level vpd we created for use below
if (clCreateRecords):
    toplevelvpd = vpd

# Loop thru our records and create our record/keyword entries
for recordItem in (sorted(recordNames.values(), key=operator.attrgetter('recordOffset'))):
    out.setIndent(2)
    recordName = recordItem.recordName

    # The little indirection needed when creating individual record files
    if (clCreateRecords):
        # Create a different vpd for use throughout below
        vpd = ET.Element("vpd")
        # Add a record and rtvpdfile to the toplevelvpd
        record = ET.SubElement(toplevelvpd, "record", {'name':recordName})
        ET.SubElement(record, "rtvpdfile").text = vpdName + "-" + recordName + ".tvpd"

    # Create our record
    record = ET.SubElement(vpd, "record", {'name':recordName})

    # Create the record description
    ET.SubElement(record, "rdesc").text = "The " + recordName + " record"

    # Start walking thru our record reading keywords out
    # As we get to each keyword, we'll create the keyword tag and it's sub tags
    recordOffset = recordItem.recordOffset

    out.msg("Record: %s" % (recordName))

    # Skip the LR tag
    recordOffset+=1

    # Get the length
    recordLength = struct.unpack('<H', vpdContents[recordOffset:(recordOffset + 2)])[0]
    recordOffset+=2

    # Now loop and read until we get until the end of the record
    recordEnd = recordOffset + recordLength
    while (recordOffset < recordEnd):
        # Read the keyword
        keywordName = vpdContents[recordOffset:(recordOffset + 2)].decode()
        recordOffset+=2

        # Determine if length is 1 or 2 bytes
        if (keywordName[0] == "#"):
            keywordLength = struct.unpack('<H', vpdContents[recordOffset:(recordOffset + 2)])[0]
            recordOffset+=2
        else:
            keywordLength = struct.unpack('<B', vpdContents[recordOffset:(recordOffset + 1)])[0]
            recordOffset+=1

        # Get the keyword data out
        keywordData = vpdContents[recordOffset:(recordOffset + keywordLength)]
        recordOffset+=keywordLength

        # If the keyword is PF, we are at the end at skip it
        if (keywordName == "PF"):
            continue

        # Create our keyword tag and subtags
        keyword = ET.SubElement(record, "keyword", {"name":keywordName})
        ET.SubElement(keyword, "kwdesc").text = "The " + keywordName + " keyword"
        ET.SubElement(keyword, "kwlen").text = str(keywordLength)
        # This is overly complicated in my opinion, but the only way I could get it to work with the time allowed
        # First strip off any trailing zero byte values.  If you don't, then it's outside the ascii range and it thinks all data is hex
        # Then try to decode the data from ascii.  If a byte is outside the range (like 0xff), it will throw the exception
        # If it doesn't throw the exception, then check to make sure the string contains only chars we allow in VPD.  Otherwise, hex

        # Walk backwords and bail the first time a nonzero value is found
        nzeroidx = len(keywordData) - 1
        while (nzeroidx >= 0):
            if (keywordData[nzeroidx] != 0x00):
                break;
            nzeroidx-=1

        # If we didn't get back to the start, shorten the data
        if (nzeroidx >= 0):
            keywordData = keywordData[0:(nzeroidx+1)]
        # Made it all the way to the start, must be all zero.  Shorten it to just the first zero byte to put into the template
        else:
            keywordData = keywordData[0:1]

        # Now try to decode and figure out hex vs ascii
        try:
            keywordData.decode('ascii')
        except UnicodeDecodeError:
            asciiState = False
        else:
            if asciiAllowed(keywordData.decode('ascii')):
                asciiState = True
            else:
                asciiState = False

        # We know if its ascii or not, store away our data
        if (asciiState):
            ET.SubElement(keyword, "kwformat").text = "ascii"
            ET.SubElement(keyword, "kwdata").text = keywordData.decode()
        else:
            ET.SubElement(keyword, "kwformat").text = "hex"
            ET.SubElement(keyword, "kwdata").text = binascii.hexlify(keywordData).decode()

        out.setIndent(4)
        out.msg("Keyword: %s Type: %5s Length: %s" % (keywordName, ("ascii" if (asciiState) else "hex"), str(keywordLength)))

    # We should be done with all the keywords, which means it's pointing to the SR tag
    if (struct.unpack('<B', vpdContents[recordOffset:(recordOffset + 1)])[0] != 0x78):
        out.error("Small resource tag not found!")
        exit(1)

    # Handle our indirection and add the record vpd to our dict for printing below
    if (clCreateRecords):
        recordTvpd[recordName] = vpd

# All done with records, cleanup our indirection
if (clCreateRecords):
    vpd = toplevelvpd

# We now have a correct tvpd, use it to create a binary VPD image
out.setIndent(0)
out.msg("==== Stage 3: Writing the tvpd output file")
out.setIndent(2)
# Create our output file names 
tvpdFileName = clOutputPath + "/" + vpdName + ".tvpd"

# This is our easy one, write the XML back out
# Write out the full template vpd representing the data contained in our image
writeTvpd(vpd, tvpdFileName)
out.msg("Wrote tvpd file: %s" % tvpdFileName)

# Now rip it through xmllint quick to cleanup formatting problems from the ET print
if (os.path.isfile("/usr/bin/xmllint")):
    rc = os.system("/usr/bin/xmllint --format %s -o %s" % (tvpdFileName, tvpdFileName))
    if (rc):
        out.error("Error occurred calling xmllint to fix xml formatting")
        exit(rc)
else:
    out.warn("xmllint not installed - no formatting cleanup done!")

# Write the sub files
if (clCreateRecords):
    # This can be in whatever order, we don't care
    for recordName in recordNames:
        
        # Create our output file names 
        tvpdFileName = clOutputPath + "/" + vpdName + "-" + recordName + ".tvpd"
        
        # This is our easy one, write the XML back out
        # Write out the full template vpd representing the data contained in our image
        writeTvpd(recordTvpd[recordName], tvpdFileName)
        out.msg("Wrote tvpd file: %s" % tvpdFileName)

        # Now rip it through xmllint quick to cleanup formatting problems from the ET print
        rc = os.system("xmllint --format %s -o %s" % (tvpdFileName, tvpdFileName))
        if (rc):
            out.error("Unable to call xmllint to fixing xml formatting")
            exit(rc)
