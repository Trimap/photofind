#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright © 2017 Juuso Räsänen <info@trimap.fi>

"""
photofind Command-line tool for finding photos based on EXIF-information.

 Usage: photofind [PATH] [PHOTO-OPTIONS] [FIND-OPTIONS]

 Author: Juuso Räsänen 2013 (email: info@trimap.fi)
 
"""

import sys
import argparse
from subprocess import Popen, PIPE

import photodb
import exiffilter


def debug(msg):
    sys.stderr.write(str(msg) + '\n')

def warn(msg):
    sys.stderr.write('Warning: ' + str(msg) + '\n')
    
def main():

    #########################################################
    # Parse command line arguments
    #########################################################

    parser = argparse.ArgumentParser(description='An extended find utility for photos.', epilog="Author: Juuso Räsänen")
    #parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)

    parser.add_argument('path', nargs='?', default='.', help="Path (default '.')")
    parser.add_argument('-videos', action='store_true', help='TODO! (Include video files also)')
    parser.add_argument('-debug', '-d', action='store_true', help='Print some additional debug info')
    parser.add_argument('-printdb', action='store_true', help='Print output in DB-format')
    parser.add_argument('-update', action='store_true', help='TODO! (Update image database for files that are not there yet.)')
    parser.add_argument('-dbfile', default=photodb.PhotoDB.DEFAULT_DBFILE, help='SimplePhotoDatabase file to use (default %s)' % photodb.PhotoDB.DEFAULT_DBFILE)
   
    exifgroup = parser.add_argument_group('Metadata filters')
    exifgroup.add_argument('-rating', help='Rating filter')
    exifgroup.add_argument('-ot', help='OrigTime filter')
    exifgroup.add_argument('-fl', help='FocalLength filter')
    exifgroup.add_argument('-f', help='F-Number filter')
    exifgroup.add_argument('-iso', help='ISO speedrating filter')
    exifgroup.add_argument('-et', help='Expossure Time filter')

    #args = parser.parse_args()
    [args, unkown_args] = parser.parse_known_args()

    extensions_filter = ' \( -iname "*.' + '" -or -iname "*.'.join(photodb.IMAGE_EXTENSIONS) + '" \) '
    size_filter = '-size +20k '
    find_opts = ''
    if len(unkown_args) > 0:
        find_opts = '"' + '" "'.join(unkown_args) + '"'
    find_cmd = 'find ' + '"' + args.path + '"' + extensions_filter + size_filter + " " + find_opts


    if (args.debug):
        debug(args)
        debug(find_cmd)


    #########################################################
    # Perform the basic finding with standard find-utility
    #########################################################
    p = Popen(find_cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, _ = p.communicate()

    files = stdout.split('\n')
    files.pop() # Remove the last - it's usually just empty line


    #########################################################
    # Perform additional filtering based on exif information
    #########################################################

    # Initialize the ExifFilter
    ef = exiffilter.ExifFilter()

    ef.add_filter('rating', args.rating)
    ef.add_filter('origtime', args.ot)
    ef.add_filter('flength', args.fl)
    ef.add_filter('aperture', args.f)
    ef.add_filter('iso', args.iso)
    ef.add_filter('exposure', args.et)

    metadataNeeded = ef.numFilters() > 0 or args.printdb

    if not metadataNeeded:
        for fname in files:
            print fname
    else:
        db = photodb.PhotoDB(args.dbfile)
        db.load()

        if args.update:
            db.setUpdateIfNotFound(True)


        nSkipped = 0
        for fname in files:
            md = db.getMetadata(fname)
            if (md == None):
                if (args.debug):
                    warn('No metadata available for %s.' % fname)
                nSkipped += 1
                continue
            else:
                ret = ef.apply(md)
                if ret:
                    if (args.printdb):
                        print fname + '\t' + str(md)
                    else:
                        print fname

        db.close()
        
        if (nSkipped > 0):
            msg = 'Skipped %d image files because they were not found in database.' % nSkipped
            if (not args.debug):
                msg += ' (Use -d option to see the skipped files.)'
            msg += '\nTip: Update the database first by running: "photodb -update %s"' % args.path
            # msg += ' Perhaps you want to run again with -update option?'
            print
            warn(msg)

if __name__ == "__main__":
    main()

