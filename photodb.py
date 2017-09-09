#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright © 2017 Juuso Räsänen <info@trimap.fi>


'''
 Created on Jan 6, 2013

 Author: Juuso Räsänen (email: info@trimap.fi)
'''
from ImageMetadata import ImageMetadata

import sqlite3

import os
import sys
import argparse
import datetime

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'tif', 'bmp', 'gif', 'xpm', 'nef', 'cr2', 'arw']


class PhotoDB:
    """ Simple Photo Database """

    DEFAULT_DBFILE = '~/.photodb.db'

    def __init__(self, dbFile=DEFAULT_DBFILE):
        self.dbFile = os.path.expanduser(dbFile)
        self.conn = None  # SQLite db connection
        self.c = None  # SQLite cursor
        self.updateIfNotFound = False
        self.isModifiedButNotSaved = False

    def isLoaded(self):
        return self.conn != None

    def load(self):
        """ Open the actual database connection. """
        self.conn = sqlite3.connect(self.dbFile)
        self.conn.text_factory = str
        self.c = self.conn.cursor()
        try:
            self.c.execute('''CREATE TABLE images(
                 filepath text PRIMARY KEY,
                 filesize integer, 
                 modtime real,
                 origtime char(20), 
                 flength real, 
                 flength35 real,                 
                 aperture real, 
                 exposure real,
                 iso real, 
                 rating integer, 
                 comment text
                 )''')

        except sqlite3.OperationalError:
            # Most obvious reason "table already exists" --> ignore
            pass
            # raise

    def close(self):
        if self.isLoaded():
            self.save()
            self.conn.close()

    def save(self):
        if not self.isLoaded():
            raise Exception("Database must be loaded before saving!")

        self.conn.commit()

    def setUpdateIfNotFound(self, val):
        # TODO
        pass

    def select(self, sqlStatementAfterWhere):
        statement = 'SELECT * FROM images WHERE %s' % sqlStatementAfterWhere
        for row in self.c.execute(statement):
            yield self.dbRowToString(row)

    def getAll(self):
        for row in self.c.execute('SELECT * FROM images'):
            yield row

    def dbRowToString(self, row):
        ret = str()
        if row:
            for elem in row:
                ret += str(elem) + "\t"
            ret.rstrip()
        return ret

    def getMetadata(self, fname):
        """ Return the metadata object for given file. """
        # TODO: Rename to getData
        fname = os.path.abspath(fname)
        self.c.execute('SELECT origtime,flength,aperture,exposure,iso,rating,comment,flength35 FROM images WHERE filepath=?', (fname,))
        row = self.c.fetchone()

        if row:
            e = ImageMetadata(fname)
            e.fromVals(dict(origtime=row[0], flength=row[1], aperture=row[2], exposure=row[3], iso=row[4], rating=row[5], comment=row[6], flength35=row[7]))
        else:
            e = None
        return e

    def getMetadataStr(self, fname):
        """ Return a string representing metadata for given file. """
        md = self.getMetadata(fname)
        return str(md)

    def setMetadata(self, fname, mdata):
        fname = os.path.abspath(fname)
        try:
            self.c.execute("INSERT INTO images VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           (fname, os.path.getsize(fname), os.path.getmtime(fname), mdata.getOrigtime(), mdata.getFocalLength(), mdata.getFocalLength35(), mdata.getAperture(), mdata.getExposure(), mdata.getIso(), mdata.getRating(), mdata.getComment()))
        except sqlite3.IntegrityError:
            self.c.execute("UPDATE images SET filesize=?, modtime=?, origtime=?, flength=?, flength35=?, aperture=?, exposure=?, iso=?, rating=?, comment=? WHERE filepath=?",
                           (os.path.getsize(fname), os.path.getmtime(fname), mdata.getOrigtime(), mdata.getFocalLength(), mdata.getFocalLength35(), mdata.getAperture(), mdata.getExposure(), mdata.getIso(), mdata.getRating(), mdata.getComment(), fname))

    def _updateFile(self, fname):
        fname = os.path.abspath(fname)

        if (self.isImage(fname)):
            self.setMetadata(fname, ImageMetadata(fname, True))

    def update(self, paths, updateEvenIfNotModified=False):
        self.load()

        if type(paths) == type(str()):
            paths = [paths]
        elif type(paths) != type(list()):
            raise TypeError("Paths must be string or list of strings!")

        numUpdated = 0
        numSkipped = 0

        for fname in PhotoDB.pathsToImageFiles(paths):
            self.c.execute('SELECT filesize, modtime FROM images WHERE filepath=?', (os.path.abspath(fname),))
            row = self.c.fetchone()

            updateNeeded = True
            if row:
                fsize = row[0]
                modtime = row[1]
                if (fsize == os.path.getsize(fname) and modtime == os.path.getmtime(fname)):
                    updateNeeded = False

            if updateNeeded or updateEvenIfNotModified:
                self._updateFile(fname)
                numUpdated += 1
                print fname
            else:
                numSkipped += 1
                #print fname + " - Skipped!"


        self.save()

        print
        print "Updated image database for %d files. Skipped %d files." % (numUpdated, numSkipped)


    def size(self):
        self.c.execute("SELECT COUNT(*) FROM images")
        return self.c.fetchone()

    def getInfo(self):
        exists = os.path.isfile(self.dbFile)

        infoStr = str()
        infoStr += "------ SimplePhotoDatabase info: ------\n"
        infoStr += "Database file: %s\n" % self.dbFile

        if exists:
            infoStr += "         size: %d bytes\n" % os.path.getsize(self.dbFile)
            infoStr += "     modified: %s\n" % datetime.datetime.fromtimestamp(os.path.getmtime(self.dbFile))

            self.load()
            infoStr += "   num photos: %d" % self.size()
        else:
            infoStr += "   Does not exist or is not a regular file..."
 
        infoStr = infoStr.rstrip()
        return infoStr

    @staticmethod
    def isImage(fname):
        _, ext = os.path.splitext(fname)
        ext = ext.lstrip('.').lower()
        if ext in IMAGE_EXTENSIONS:
            return True
        else:
            return False

    @staticmethod
    def pathsToFiles(paths):
        """ Find the files behind given paths (i.e. files or dirs). """
        for path in paths:
            if os.path.isfile(path):
                yield path
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    # Ignore hidden directories
                    dirs[:] = [dn for dn in dirs if not dn.startswith('.')]

                    for ff in files:
                        if (not ff.startswith('.')):
                            yield os.path.join(root, ff)
            else:
                sys.stderr.write('Warning: Neither a file nor directory: %s \n' % path)

    @staticmethod    
    def pathsToImageFiles(paths):
        for f in PhotoDB.pathsToFiles(paths):
            if PhotoDB.isImage(f):
                yield f        

def main():

    parser = argparse.ArgumentParser(description='photodb - Simple Photo Database', epilog="Copyright: Juuso Räsänen")
    parser.add_argument('-debug', '-d', action='store_true', help='Print some additional debug messages')

    pathsGroup = parser.add_argument_group('Paths')
    pathsGroup.add_argument('paths', nargs='*', metavar='PATH', help="File system path (to image file(s)) for operation.")
    modeGroup = parser.add_argument_group('Mode')
    group = modeGroup.add_mutually_exclusive_group()
    group.add_argument('-update', action='store_true', help='Update database for given path(s)')
    group.add_argument('-check', action='store_true', help='Check if database is up-to-date for given path(s)')
    group.add_argument('-info', action='store_true', help='Print database info and exit. (default if no paths)')
    group.add_argument('-show', action='store_true', help='Show contents for given path(s) (default if paths given)')
    group.add_argument('-select', help='SQL select statement. E.g. "flength>100 AND rating>2"')

    parser.add_argument('-force', action='store_true', help='Update even if not modified')
    parser.add_argument('-dbfile', default=PhotoDB.DEFAULT_DBFILE, help='Database file to use (default %s)' % PhotoDB.DEFAULT_DBFILE)

    args = parser.parse_args()

    # Set the default working mode (manually, perhaps could be set by argparse somehow?)
    if (args.update + args.check + args.info + args.show + int(args.select != None)) == 0:
        if len(args.paths) == 0:
            args.info = True
        else:
            args.show = True
    
    if (args.update or args.check or args.show) and len(args.paths) == 0:
        parser.print_usage()
        sys.stderr.write('Error: No paths given!\n')
        return 1

    if args.debug:
        pass

    db = PhotoDB(args.dbfile)

    if args.info:
        print db.getInfo()
    elif args.update:
        db.update(args.paths, args.force)
    elif args.check:
        print "Check behavior is TODO!"
    elif args.select:
        db.load()
        for row in db.select(args.select):
            print row
    elif args.show:
        db.load()
        for fname in PhotoDB.pathsToFiles(args.paths):
            print fname + "\t" + db.getMetadataStr(fname)
    else:
        sys.stderr.write('Error! Perhaps problems while parsing arguments?\n')

    db.close()


if __name__ == "__main__":
    main()
