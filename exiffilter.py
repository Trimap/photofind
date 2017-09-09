# -*- coding: utf-8 -*-

"""
 Author: Juuso Räsänen 2013 (email: info@trimap.fi)

"""

import fractions

import ImageMetadata


class Filter:
    EQ=0 # Equal
    NE=1 # Not-equal
    LT=2 # Less-than
    LE=3 # Less-or-equal
    GT=4 # Greater-than
    GE=6 # Greater-or-equal
    #EX=7 # Exists (?) --> Use GT && self.refval = None instead.

    def __init__(self, filter_string, datatype):
        self.datatype = datatype
        self.filtertype = Filter.GT
        self.refval = None
        self.userdata = None
        self.parse_filter(filter_string)
        
    def apply(self, data):
        """ Apply this filter on given data. Return true if pass, false otherwise. """

        if (self.refval == None):
            return data != None

        if (type(data) == type(None)):
            return False

        refval = self.refval
        curval = self.parse_value(data)
        #print "'%s' '%s'" % (refval, curval)
        if (self.filtertype == Filter.GT):
            return curval > refval
        if (self.filtertype == Filter.LT):
            return curval < refval
        if (self.filtertype == Filter.EQ):
            return curval == refval
        if (self.filtertype == Filter.GE):
            return curval >= refval
        if (self.filtertype == Filter.LE):
            return curval <= refval

    def parse_filter(self, filter_string):
        nc = 0
        if (len(filter_string) == 0):
            # "Exists-filter"
            self.filtertype = Filter.GT
            self.refval = None
            return
        elif filter_string[0] == '+':
            if (len(filter_string) > 1 and filter_string[1] == '='):
                self.filtertype = Filter.GE
                nc = 2
            else:
                self.filtertype = Filter.GT
                nc = 1
        elif filter_string[0] == '-':
            if (len(filter_string) > 1 and filter_string[1] == '='):
                self.filtertype = Filter.LE
                nc = 2
            else:
                self.filtertype = Filter.LT
                nc = 1
        else:
            self.filtertype = Filter.EQ

        self.refval = self.parse_value(filter_string[nc:])

    def parse_value(self, val):
        """ Parse value of defined datatype from given string. """

        if (self.datatype == type(float())):
            if (type(val).__name__ == 'Rational'):
                return val.to_float()

            # Support also setting float values as rational numbers
            if (type(val) == type(str())):
                return float(fractions.Fraction(val))
        
        # This is the default case
        return self.datatype(val)


class ExifFilter:
    def __init__(self):
        self.filters = []

    def add_filter(self, field_string, filter_string):

        if (filter_string == None):
            return

        datatype = ImageMetadata.TYPES[field_string]

        f = Filter(filter_string, datatype)
        f.userdata = field_string    # Store the metadata field in the userdata

        self.filters.append(f)

    def numFilters(self):
        return len(self.filters)

    def apply(self, metadata):
        """ Apply this filter on given data. Return true if pass, false otherwise. """
        ret = True
        for f in self.filters:
            val = metadata[f.userdata]
            ret &= f.apply(val)

        return ret

