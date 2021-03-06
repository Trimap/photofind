# photofind
A simple Linux CLI tool for finding/filtering image files based on their EXIF information.

So basically this is like the traditional Unix [find-command](https://linux.die.net/man/1/find) but with added ability to use also EXIF-information for filtering the results. Written in python.

**Note 2017-09-09**: This tool was originally created for personal purposes in 2013 and made public today (2017-09-09). **If you like it and want to develop/maintain it further, please let me know!** (I don't personally have time for this right now). Wouldn't it be great to have such a tool as part of mainstream Linux distributions? ;)

The codebase hasn't been maintained much since 2013 but it should work as shown by the examples below.

## Installation
Install dependecies (e.g. in Ubuntu):
`sudo apt install python python-pyexiv2`

Then just clone the repository and you should be ready to go.

Additionally you could to add symbolic links to `photofind.py` and `photodb.py` files to somewhere in your PATH to make the usage more convenient.

## Basic Examples
 _This set of examples doesn't involve any EXIF-based stuff. So all these queries are done by using the reqular find-command under the hood._

To print usage:
`./photofind.py -h`

To print usage for the related photodb-tool:
`./photodb.py -h`

To find all image files in certain directory ("~/Pictures" in this case):
`./photofind.py ~/Pictures/`

To find image files whose size is bigger than 5 MB:
`./photofind.py ~/Pictures/ -size +5M`

To count the number of image files bigger than 5MB:
(Demonstrates piping to other commands)
`./photofind.py ~/Pictures/ -size +5M | wc -l`

## EXIF Examples
First update the database first for given path:
`./photodb.py -update ~/Pictures/`

To see the database info (size, number of photos etc.):
`./photodb.py`

To find photos whose ISO setting is over 400:
`./photofind.py ~/Pictures/ -iso +400`

To find photos whose focal length is 200 or over and user rating is 3:
`./photofind.py ~/Pictures/ -fl +=100  -rating 3`

## How it works

The photofind utility works internally in 2 passes. In the first pass it executes find command with parameters like:

`find ~/Pictures \( -iname "*.jpg" -or -iname "*.jpeg" -or -iname "*.png" -or -iname "*.tif" -or -iname "*.bmp" -or -iname "*.gif" -or -iname"*.xpm" -or -iname "*.nef" -or -iname "*.cr2" -or -iname "*.arw" \) -size +20k`

Then in the second pass it filters the files of the previous command based on their EXIF information. The EXIF data is read from the files but cached in simple SQLite database (stored in file `~/.photodb.db` by default) to speed-up the queries.
Ideally this caching could be transparent to the user (so there wouldn't be need to call photodb.py manually) but this is currently not implemented.
