from __future__ import print_function
import glob
import re
import os
import json
import subprocess
import argparse
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
        # Set disk GUID type to Ceph Jorunal for fixing wrong journal permission.
        subprocess.call('sgdisk -t %s:45B0969E-9B03-4F30-B4C6-B4B80CEFF106 %s' % (i+1, dev), shell=True)
        start = start + journal_size_in_sectors
    if bcache:
        create_partition_s(dev, 'bcache', start, '100%')

def create_equal_partitions(blockdevice, wipe, number_of_partitions):
    print('creating equal partitions')

def create_journals(blockdevice, wipe, number_of_partitions):
    if wipe:
        wipe_disk(blockdevice)
    auto_partition(blockdevice, number_of_partitions)
    print('creating journal partitions')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A wrapper around parted for easier operations')
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-e', '--equal', help='partition the drive into equal partitions', action='store_true')
    action_group.add_argument('-j', '--journals', help='create a number of fixed size partitions', action='store_true')
    parser.add_argument('-n', '--number-of-partitions', help='how many partitions to create', required=True)
    parser.add_argument('--do-not-wipe', help='do not wipe the physical block device', action='store_false')
    parser.add_argument('-b', '--block-device', help='target block device', required=True)
    args = parser.parse_args()
    if args.equal:
        create_equal_partitions(args.block_device, args.do_not_wipe, args.number_of_partitions)
    elif args.journals:
        create_journals(args.block_device, args.do_not_wipe, args.number_of_partitions)
