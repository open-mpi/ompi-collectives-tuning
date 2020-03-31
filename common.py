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
        from string import strip, split
        self.m_params = {}
        f = open(filnam)
        l = f.readline()
        while len(l):
            if l[0]!='#':
                itmlst = split(l, ":")
                if len(itmlst)==2:
                    self.m_params[strip(itmlst[0])] = strip(itmlst[1])

            l = f.readline()

    def getStr(self, key):
        return self.m_params[key]

    def getStrlst(self, key):
        from string import split
        return split(self.m_params[key])

    def getInt(self, key):
        from string import atoi
        return atoi(self.getStr(key))

    def getIntlst(self, key):
        from string import atoi, split
        strlst = split(self.getStr(key))
        intlst = [atoi(s) for s in strlst]
        return intlst

    def getFloatlst(self, key):
        from string import split
        strlst = split(self.getStr(key))
        floatlst = [float(s) for s in strlst]
        return floatlst
