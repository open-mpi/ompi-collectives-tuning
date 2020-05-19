# Copyright (c) 2020      Amazon.com, Inc. or its affiliates.  All Rights
#                         reserved.
#
# $COPYRIGHT$
#
# Additional copyrights may follow
#
# $HEADER$
#

class Params:

    def __init__(self, filnam):
        self.m_params = {}
        f = open(filnam)
        l = f.readline()
        while len(l):
            if l[0]!='#':
                itmlst = l.split( ":", 1)
                if len(itmlst)==2:
                    self.m_params[itmlst[0].strip()] = itmlst[1].strip()

            l = f.readline()

    def getStr(self, key):
        return self.m_params[key]

    def getStrlst(self, key):
        return self.m_params[key].split()

    def getInt(self, key):
        return int(self.getStr(key))

    def getIntlst(self, key):
        strlst = self.getStr(key).split()
        intlst = [int(s) for s in strlst]
        return intlst

    def getFloatlst(self, key):
        strlst = self.getStr(key).split()
        floatlst = [float(s) for s in strlst]
        return floatlst
