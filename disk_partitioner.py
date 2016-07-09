from __future__ import print_function
import glob
import re
import os
import json
import subprocess
import sys

def size(device):
    nr_sectors = open(device+'/size').read().rstrip('\n')
    sect_size = open(device+'/queue/hw_sector_size').read().rstrip('\n')

    # The sect_size is in bytes, so we convert it to GiB and then send it back
    return (float(nr_sectors)*float(sect_size))/(1000.0*1000.0*1000.0)

def chunks(l, n):
    newn = int(len(l) / n)
    for i in xrange(0, n-1):
        yield l[i*newn:i*newn+newn]
    yield l[n*newn-newn:]

def wipe_disk(disk):
    subprocess.call('parted -s %s mklabel gpt' % disk, shell=True)

# size is in sectors
def create_partition_s(dev, name, start, end):
    subprocess.call('parted -s %s unit s mkpart %s %s %s' % (dev, name, start, end), shell=True)

# would be nice to have a debug flag...
#    print('parted -s -a optimal %s unit s mkpart %s %s %s' % (dev, name, start, end))

# Currently the code only handles 512 byte sectors.
# Fix size() and use it here to make it more roboust.
def auto_partition(dev, n_osds, journal_size=10*1024*1024*1024, sector_size=512, bcache=False):
    start = 2048 # we need to align our partitions - this is 1MB (2048 * 512 = 1MB)
    journal_size_in_sectors = journal_size / sector_size
    for i in range(0, n_osds):
        create_partition_s(dev, 'journal', start, start + journal_size_in_sectors - 1)
        start = start + journal_size_in_sectors
    if bcache:
        create_partition_s(dev, 'bcache', start, '100%')

if __name__ == "__main__":
    wipe_disk(sys.argv[1])
    auto_partition(sys.argv[1], 12)
