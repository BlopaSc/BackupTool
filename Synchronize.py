# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import argparse
import os
import shutil
import sys

def list_files(directory, exclude = []):
    files = list()
    try:
        for name in os.listdir(directory):
            cname = directory+'/'+name
            if os.path.isdir(cname):
                for i in list_files(cname):
                    files.append(name+'/'+i)
            else:
                files.append(name)
    except PermissionError:
        pass
    return files

def filter_files(files, exclude):
    files.sort()
    exclude.sort()
    filtered = []
    f_idx, ex_idx = 0,0
    while f_idx < len(files) and ex_idx < len(exclude):
        if files[f_idx] < exclude[ex_idx]:
            filtered.append(files[f_idx])
            f_idx += 1
        elif files[f_idx].startswith(exclude[ex_idx]):
            f_idx += 1
        else:
            ex_idx += 1
    while f_idx < len(files):
        filtered.append(files[f_idx])
        f_idx += 1
    return filtered

def calculate_differences(srcfiles, dstfiles, srcpath, dstpath):
    srcfiles = set(srcfiles)
    dstfiles = set(dstfiles)
    add = srcfiles - dstfiles
    remove = dstfiles - srcfiles
    update = set()
    for file in srcfiles & dstfiles:
        if os.path.getmtime(srcpath + '/' + file) != os.path.getmtime(dstpath + '/' + file):
            update.add(file)
    return list(add),list(update),list(remove)

def copy_file(srcpath, dstpath):
    try:
        shutil.copy2(srcpath, dstpath)
    except FileNotFoundError:
        make_directory(dstpath[:dstpath.rfind('/')])
        shutil.copy2(srcpath, dstpath)

def make_directory(path):
    try:
        os.mkdir(path)
    except FileNotFoundError:
        make_directory(path[:path.rfind('/')])
        os.mkdir(path)

def copy_files(files, srcpath, dstpath, verbose):
    for file in files:
        print(f"Copying: {file}")
        copy_file(srcpath + '/' + file, dstpath + '/' + file)
        
def remove_files(files, dstpath, verbose):
    for file in files:
        print(f"Removing: {file}")
        dstfile = dstpath + '/' + file
        os.remove(dstfile)
        check_directory(dstfile[:dstfile.rfind('/')])

def check_directory(path):
    if len(os.listdir(path)) == 0:
        os.rmdir(path)
        check_directory(path[:path.rfind('/')])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Synchronize', description='Easy to use backup tool for handling directories. Allows to automatically copy the new and modified files from a source directory into a destination directory; allows to automatically remove no-longer existing files in the source directory that exist on the destination directory.')
    parser.add_argument('-s', '--src', required=True, help='source directory where the files to backup are stored.')
    parser.add_argument('-d', '--dst', required=True, help='destination directory where the files to backup will be stored.')
    parser.add_argument('-a', '--apply', action='store_true', help='instead of merely listing the changes that are needed to keep the backup up-to-date, it applies those changes automatically.')
    parser.add_argument('-f', '--force', action='store_true', help='disables the confirmation steps before performing the copy/update/remove operations.')
    parser.add_argument('-v', '--verbose', type=int, default=1, help='specifies the level of verbose to utilize, if the changes are not being applied the minimum verbose is 1.')
    parser.add_argument('-x', '--exclude', default='', help='list of paths separated by ? to exclude from the process both in source and destination.')
    args = parser.parse_args()
    
    verbose = max(args.verbose,not args.apply)
        
    if not os.path.exists(args.src):
        print("Error: Source path does not exist")
        sys.exit(1)
    
    if not os.path.exists(args.dst):
        print("Error: Destination path does not exist")
        sys.exit(1)
        
    if os.path.abspath(args.src) == os.path.abspath(args.dst):
        print("Error: Source and destination cannot be the same")
        sys.exit(1)
    elif os.path.abspath(args.src).startswith(os.path.abspath(args.dst)):
        print("Error: Source cannot be a subdirectory of destination")
    elif os.path.abspath(args.dst).startswith(os.path.abspath(args.src)):
        print("Error: Destination cannot be a subdirectory of source")
    
    if verbose>1:
        print(f"Source: {args.src}")
        print(f"Destination: {args.dst}")
    
    srcpath = args.src
    dstpath = args.dst
    
    srcpath = srcpath.replace('\\','/')
    dstpath = dstpath.replace('\\','/')
    
    if srcpath.endswith('/'): srcpath = srcpath[:-1]
    if dstpath.endswith('/'): dstpath = dstpath[:-1]
    
    srcfiles = list_files(srcpath)
    dstfiles = list_files(dstpath)
    
    exclude = [p for p in args.exclude.split('?') if p]
    
    if sys.platform.startswith('win'):
        exclude.append('$RECYCLE.BIN')
    
    if verbose>1 and exclude:
        separator = '\n\t\t\t'
        print(f"Excluding:\t{separator.join(exclude)}")
    
    srcfiles = filter_files(srcfiles, exclude)
    dstfiles = filter_files(dstfiles, exclude)
    
    add,update,remove = calculate_differences(srcfiles, dstfiles, srcpath, dstpath)
    add.sort()
    update.sort()
    remove.sort()
    
    if verbose>1:
        print(f"Search found a total of:\n\t\t\t{len(add)} new files\n\t\t\t{len(update)} modified files\n\t\t\t{len(remove)} deleted files")
        
    if (not args.apply) and args.verbose>0:
        for file in add:
            print(f"new: {file}")
        for file in update:
            print(f"modified: {file}")
        for file in remove:
            print(f"deleted: {file}")
        
    if args.apply:
        apply = True
        if not args.force:
            ans = ''
            while not ans in ['y','n']:
                ans = input("Do you want to apply the changes?\n\ty - yes\t\tto accept\n\tn - no\t\tto decline\n\tt - totals\tto see the total changes\n\tl - list\tto get the list of all changes\n").lower()
                if ans: ans = ans[0]
                if ans == 't':
                    print(f"Search found a total of:\n\t\t\t{len(add)} new files\n\t\t\t{len(update)} modified files\n\t\t\t{len(remove)} deleted files")
                elif ans == 'l':
                    for file in add:
                        print(f"new: {file}")
                    for file in update:
                        print(f"modified: {file}")
                    for file in remove:
                        print(f"deleted: {file}")
                elif ans == 'n':
                    apply = False
        if apply:
            if verbose>1: print("Applying changes:")
            copy_files(add,srcpath,dstpath,verbose=verbose>1)
            copy_files(update,srcpath,dstpath,verbose=verbose>1)
            remove_files(remove,dstpath,verbose=verbose>1)
