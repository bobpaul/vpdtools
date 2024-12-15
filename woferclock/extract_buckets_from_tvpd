#!/usr/bin/env python2
#
# Copyright (c) 2018 Raptor Engineering, LLC
# Released under the terms of the AGPL v3

import sys
from xml.dom import minidom
xmldoc = minidom.parse(sys.argv[2])
recordlist = xmldoc.getElementsByTagName('keyword')
for r in recordlist:
    if r.attributes['name'].value == sys.argv[1]:
        datalist = r.getElementsByTagName('kwdata')
        for d in datalist:
            print d.childNodes[0].nodeValue
