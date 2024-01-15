#!/usr/bin/env python
"""
This script synchronizes two folders

Usage: folder_synchronizer.py -h

© Jakub Maly 2024
"""

import argparse
from pathlib import Path
import time
import hashlib
import shutil
import logging
import sys

def synchronize(source_path, replica_path, logger):
    """
    Function synchronizing given folders.

    Warning: Recursion possible!
    """

    logger.info('Checking %s to reflect %s', replica_path.resolve(), source_path.resolve())

    source_objects = source_path.glob('*')
    replica_objects = replica_path.glob('*')

    # Obtain distinct objects if they exist.
    source_objects_set = set(source_object.name for source_object in source_objects)
    replica_objects_set = set(replica_object.name for replica_object in replica_objects)
    distinct_objects_set = source_objects_set ^ replica_objects_set

    # Reobtain objects.
    source_objects = source_path.glob('*')

    # Remove them if they are in replica folder.
    for distinct_object in distinct_objects_set:
        old_object_path = replica_path / distinct_object
        if old_object_path.exists():
            logger.warning('Removing %s', old_object_path.resolve())

            # Old object is directory.
            if old_object_path.is_dir():
                shutil.rmtree(old_object_path)

            # Old object is file.
            else:
                old_object_path.unlink()

    # Synchronize.
    for source_object in source_objects:
        # Target paths.
        source_target_path = source_path / source_object.name
        replica_target_path = replica_path / source_object.name

        # Object is directory.
        if source_object.is_dir():
            # It does not exist.
            if not replica_target_path.exists():
                logger.warning('Creating %s', replica_target_path.resolve())
                replica_target_path.mkdir()

            # Recursion.
            synchronize(source_target_path, replica_target_path, logger)

        # Object is file.
        else:
            # Replica exists.
            if replica_target_path.exists():
                # Source hash.
                source_hash = hashlib.md5()
                source_hash.update(source_target_path.read_bytes())
                source_hash = source_hash.hexdigest()

                # Replica hash.
                replica_hash = hashlib.md5()
                replica_hash.update(replica_target_path.read_bytes())
                replica_hash = replica_hash.hexdigest()

                # Replica does not match.
                if source_hash != replica_hash:
                    logger.warning('Updating %s', replica_target_path.resolve())
                    shutil.copy(source_target_path, replica_target_path)

            # Replica does not exists.
            else:
                logger.warning('Adding %s', replica_target_path.resolve())
                shutil.copy(source_target_path, replica_target_path)

def main(source_folder, replica_folder, poll_interval, log_file_str, verbosity):
    """
    Main function of the program.
    """

    # Set logging.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(verbosity * 10)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file_str)
    file_handler.setLevel(verbosity * 10)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    # Check source path.
    source_path = Path(source_folder)
    assert(source_path.exists()), f'{source_path} - Path to the source folder is incorrect!'

    # Check replica path.
    replica_path = Path(replica_folder)
    if not replica_path.exists():
        replica_path.mkdir()

    # Check poll interval.
    if 0 == poll_interval:
        # Synchronize folders.
        synchronize(source_path, replica_path, logger)
    else:
        while True:
            # Synchronize folders.
            synchronize(source_path, replica_path, logger)

            # Wait for next.
            logger.info('Entering %ds sleep', poll_interval)
            time.sleep(poll_interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s',
                        '--source',
                        help='path to the source folder',
                        default='source_folder')
    parser.add_argument('-r',
                        '--replica',
                        help='path to the replica folder',
                        default='replica_folder')
    parser.add_argument('-p',
                        '--poll',
                        help='synchronization poll interval in seconds',
                        type=int,
                        default=0,
                        choices=range(0, 61))
    parser.add_argument('-l',
                        '--log',
                        help='path to the log file',
                        default='folder_synchronizer.log')
    parser.add_argument('-v',
                        '--verbose',
                        help='level of verbosity (\0 = NOTSET, 1 = DEBUG, 2 = INFO, 3 = WARNING, \
                              4 = ERROR, 5 = CRITICAL)',
                        type=int,
                        default=3,
                        choices=range(0, 6))
    args = parser.parse_args()

    main(args.source, args.replica, args.poll, args.log, args.verbose)
