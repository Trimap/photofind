'''
Created on Jan 5, 2013

@author: juuso
'''

import pyexiv2
import sys
import re
from fractions import Fraction

# Define the supported SimpleDataBase keys and their mapping to Exiv2/Metadata fields.
KEYS = dict()
TYPES = dict()
KEYS['origtime'] = ['Exif.Photo.DateTimeOriginal']
TYPES['origtime'] = type(str())
KEYS['comment'] = ['Exif.Image.ImageDescription']
TYPES['comment'] = type(str())
KEYS['aperture'] = ['Exif.Photo.FNumber']
TYPES['aperture'] = type(float())
KEYS['flength'] = ['Exif.Photo.FocalLength']
TYPES['flength'] = type(float())
KEYS['flength35'] = ['Exif.Photo.FocalLengthIn35mmFilm']
TYPES['flength35'] = type(float())
KEYS['exposure'] = ['Exif.Photo.ExposureTime']
TYPES['exposure'] = type(float())
KEYS['iso'] = ['Exif.Photo.ISOSpeedRatings', 'Exif.Nikon3.ISOSpeed']
TYPES['iso'] = type(float())
KEYS['rating'] = ['Xmp.xmp.Rating']
TYPES['rating'] = type(int())

class ImageMetadata:
    """ Class for metadata of a single file, i.e. a data-base-entry. """

    disable_stderr = True
 
    def __init__(self, fname, readNow=False):
        self.fname = fname
        self.data = dict()
        self.exiv2md = None
        if readNow:
            self.read()

    def __str__(self):
        """ Return this entry in the SDB - format. """

        dbrow = "" # self.fname

        if (self.data):
            for k in KEYS:
                if (self.data.has_key(k)):
                    dbrow += '%s=%s\t' % (k,self.data[k])     
        else:
            sys.stderr.write('Error (%s): Metadata is not read !\n' % self.fname)
            for k in KEYS.keys():
                dbrow += '%s=None\t' % k
        
        dbrow = dbrow.rstrip() # Remove the trailing '\t'
        
        return dbrow

    def fromString(self, DBEntry):
        """ Read metadata values from given SDB-string. """
        vals = re.findall('([^\t]*?)=(.*?)(?:\t|$)', DBEntry)
        for (key, val) in vals:
            try:
                self.data[key] = TYPES[key](val)
            except ValueError:
                self.data[key] = None
    
    def clear(self):
        self.data.clear()
        pass
    
    # origtime=None, aperture=None, iso=None, exposure=None, flength=None, rating=None, comment=None
    def fromVals(self, valsDict):
        self.clear()
        for key in valsDict:
            val = valsDict[key]
            if (KEYS.has_key(key)):
                if (val != None):
                    self.data[key] = TYPES[key](val)
            else:
                sys.stderr.write('Warn: Ingoring unsupported metadata key "%s". \n' % key)
                

    def read(self):
        """ Read the real up-to-date metadata values from the file. """
        self.clear()

        try:
            self.exiv2md = pyexiv2.ImageMetadata(unicode(self.fname, encoding=sys.getfilesystemencoding()))
        except UnicodeDecodeError, msg:
            sys.stderr.write('Error (%s): %s\n' % (self.fname, msg))
            return

        try:
            self.exiv2md.read()

        except IOError, msg:
            sys.stderr.write('Error reading metadata: %s\n' % msg)
            return
        
        for key in KEYS:
            for exifkey in KEYS[key]:
                val = self.getExivField(exifkey)
                if (val != None):
                    try:
                        self.data[key] = TYPES[key](val)
                        continue
                    except ValueError:
                        # This might happen e.g. is the read image file was corrupted.
                        pass
                    except TypeError:
                        pass

    def __getitem__(self, k):
        try:
            return self.data[k]
        except KeyError:
            # sys.stderr.write('Error: Not loaded or unsupported key "%s".\n' % k)
            return None

    def getExposure(self):
        return self.__getitem__('exposure')

    def getAperture(self):
        try:
            return float(self.__getitem__('aperture'))
        except TypeError:
            return None

    def getIso(self):
        try:
            return float(self.__getitem__('iso'))
        except TypeError:
            return None

    def getFocalLength(self):
        try:
            return float(self.__getitem__('flength'))
        except TypeError:
            return None

    def getFocalLength35(self):
        try:
            return float(self.__getitem__('flength35'))
        except TypeError:
            return None
        
    def getRating(self):
        try:
            return int(self.__getitem__('rating'))
        except TypeError:
            return None

    def getComment(self):
        val = self.__getitem__('comment')
        if (val != None):
            return val
        else:
            return None

    def getOrigtime(self):
        return str(self.__getitem__('origtime'))
            
    def getExivField(self, exivKey):
        if (not self.exiv2md):
            sys.stderr.write('Error (%s): Metadata values should be read before accessing them.\n' % self.fname)
            #raise Exception('Metadata values must be read before accessing them.')
            return None

        try:
            #val = self.exiv2md[exivKey].value
            val = self.exiv2md[exivKey]
            
            if (val.type == 'Rational'):
                ret = Fraction(str(val.value))
                #ret = val.value.to_float()
            elif (exivKey == 'Exif.Photo.ISOSpeedRatings' and val.type == 'Short'):
                ret = val.human_value   # This is workaround for Nikon ISOSpeed fields which are 'list of Shorts'
            else:
                ret = val.value

        except KeyError, msg:
            #val = str(msg)
            ret = None
        return ret