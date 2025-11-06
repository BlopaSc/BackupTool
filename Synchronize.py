# -*- coding: utf-8 -*-
"""
@author: Blopa
"""

import argparse
import hashlib
import os
import shutil
import sys

def hash_file(filename):
    file_hash = hashlib.md5()
    with open(filename, "rb") as f:
        while chunk := f.read(8388608):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def list_files(directory, exclude = []):
    files = list()
    empty_dirs = list()
    try:
        lstdir = os.listdir(directory)
        for name in lstdir:
            cname = directory+'/'+name
            if os.path.isdir(cname):
                child_files, child_empty = list_files(cname)
                if len(child_files) > 0 or len(child_empty) > 0:
                    for i in child_files:
                        files.append(name+'/'+i)
                    for i in child_empty:
                        empty_dirs.append(name+'/'+i)
                else:
                    empty_dirs.append(name)
            else:
                files.append(name)
    except PermissionError:
        pass
    return files, empty_dirs

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
    metadata_repair_src = set()
    metadata_repair_dst = set()
    for file in srcfiles & dstfiles:
        srctime = os.path.getmtime(srcpath + '/' + file)
        dsttime = os.path.getmtime(dstpath + '/' + file)
        if srctime!=dsttime:
            srchash = hash_file(srcpath + '/' + file)
            dsthash = hash_file(dstpath + '/' + file)
            if srchash == dsthash:
                if srctime<dsttime:
                    metadata_repair_dst.add(file)
                else:
                    metadata_repair_src.add(file)
            else:
                update.add(file)
    return list(add),list(update),list(remove),list(metadata_repair_src),list(metadata_repair_dst)

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
        if verbose: print(f"Copying: {file}")
        copy_file(srcpath + '/' + file, dstpath + '/' + file)
        
def remove_files(files, dstpath, verbose):
    for file in files:
        if verbose: print(f"Removing: {file}")
        dstfile = dstpath + '/' + file
        os.remove(dstfile)
        check_directory(dstfile[:dstfile.rfind('/')])

def check_directory(path):
    if len(os.listdir(path)) == 0:
        os.rmdir(path)
        check_directory(path[:path.rfind('/')])

def remove_empty(empty_paths, dstpath, verbose, typ):
    for path in empty_paths:
        if verbose: print(f"Removing {typ} empty dir: {path}")
        check_directory(dstpath + '/' + path)
    
def copy_metadata(files, srcpath, dstpath, verbose, typ):
    for file in files:
        if verbose: print(f"Repairing {typ} metadata {file}")
        shutil.copystat(srcpath + '/' + file, dstpath + '/' + file)
    
        
def print_files(typ, files):
    for file in files:
        print(f"{typ}: {file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Synchronize', description='Easy to use backup tool for handling directories. Allows to automatically copy the new and modified files from a source directory into a destination directory; allows to automatically remove files in the destination directory that no longer exist in the source directory.')
    parser.add_argument('-s', '--src', required=True, help='source directory from where to read the files to backup.')
    parser.add_argument('-d', '--dst', required=True, help='destination directory in where to store the files to backup.')
    parser.add_argument('-a', '--apply', action='store_true', help='instead of merely listing the changes that are needed to keep the backup up-to-date, it applies those changes automatically.')
    parser.add_argument('-f', '--force', action='store_true', help='disables the confirmation steps before performing the copy/update/remove operations.')
    parser.add_argument('-e', '--empty', action='store_true', help='deletes empty directories in both soure and destination')
    parser.add_argument('-m', '--meta', action='store_true', help='enables metadata repair for files, if two files are identical then the older metadata is copied (applies to both src and dst)')
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
    
    exclude = [p for p in args.exclude.split('?') if p]
    
    if sys.platform.startswith('win'):
        exclude.append('$RECYCLE.BIN')
    
    if verbose>1 and exclude:
        separator = '\n\t\t\t'
        print(f"Excluding:\t{separator.join(exclude)}")
    
    srcfiles,srcdirs = list_files(srcpath)
    dstfiles,dstdirs = list_files(dstpath)
    
    srcfiles = filter_files(srcfiles, exclude)
    dstfiles = filter_files(dstfiles, exclude)
    
    add,update,remove,metadata_repair_src,metadata_repair_dst = calculate_differences(srcfiles, dstfiles, srcpath, dstpath)
    add.sort()
    update.sort()
    remove.sort()
    metadata_repair_src.sort()
    metadata_repair_dst.sort()
    
    if verbose>1:
        print("Search found a total of:")
        print(f"\t\t\t{len(add)} new files")
        print(f"\t\t\t{len(update)} modified files")
        print(f"\t\t\t{len(remove)} deleted files")
        print(f"\t\t\t{len(srcdirs)} empty directories in source")
        print(f"\t\t\t{len(dstdirs)} empty directories in destination")
        print(f"\t\t\t{len(metadata_repair_src)} metadata repair files in source")
        print(f"\t\t\t{len(metadata_repair_dst)} metadata repair files in destination")
        
    if (not args.apply) and args.verbose>0:
        print_files("new", add)
        print_files("modified", update)
        print_files("deleted", remove)
        if args.empty:
            print_files("source empty dir", srcdirs)
            print_files("dest empty dir", dstdirs)
        if args.meta:
            print_files("source repair", metadata_repair_src)
            print_files("dest repair", metadata_repair_dst)
        
    if args.apply:
        if len(add)+len(update)+len(remove)+args.meta*len(metadata_repair_src)+args.meta*len(metadata_repair_dst) == 0:
            if verbose > 1: print("Backup is up-to-date")
            sys.exit(0)
        apply = True
        if not args.force:
            ans = ''
            while not ans in ['y','n']:
                ans = input("Do you want to apply the changes?\n\ty - yes\t\tto accept\n\tn - no\t\tto decline\n\tt - totals\tto see the total changes\n\tl - list\tto get the list of all changes\n").lower()
                if ans: ans = ans[0]
                if ans == 't':
                    print("Search found a total of:")
                    print(f"\t\t\t{len(add)} new files")
                    print(f"\t\t\t{len(update)} modified files")
                    print(f"\t\t\t{len(remove)} deleted files")
                    print(f"\t\t\t{len(srcdirs)} empty directories in source")
                    print(f"\t\t\t{len(dstdirs)} empty directories in destination")
                    print(f"\t\t\t{len(metadata_repair_src)} metadata repair files in source")
                    print(f"\t\t\t{len(metadata_repair_dst)} metadata repair files in destination")
                elif ans == 'l':
                    print_files("new", add)
                    print_files("modified", update)
                    print_files("deleted", remove)
                    if args.empty:
                        print_files("source empty dir", srcdirs)
                        print_files("dest empty dir", dstdirs)
                    if args.meta:
                        print_files("source repair", metadata_repair_src)
                        print_files("dest repair", metadata_repair_dst)
                elif ans == 'n':
                    apply = False
        if apply:
            if verbose>1: print("Applying changes:")
            remove_files(remove,dstpath,verbose=verbose>1)
            copy_files(add,srcpath,dstpath,verbose=verbose>1)
            copy_files(update,srcpath,dstpath,verbose=verbose>1)
            if args.empty:
                _,srcdirs = list_files(srcpath)
                _,dstdirs = list_files(dstpath)
                remove_empty(srcdirs, srcpath, verbose=verbose>1, typ='src')
                remove_empty(dstdirs, dstpath, verbose=verbose>1, typ='dst')
            if args.meta:
                copy_metadata(metadata_repair_src, dstpath, srcpath, verbose=verbose>1, typ='src')
                copy_metadata(metadata_repair_dst, srcpath, dstpath, verbose=verbose>1, typ='dst')
