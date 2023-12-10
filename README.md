# Backup Tool

Backup Tool by Blopa Sauma is an easy to use backup tool for handling directories. The tool allows to syncronize a source and a destination directory in the following way:

- Detects and allows to automatically copy the new and modified files from a source directory into a destination directory.
- Detects and allows to automatically remove files in the destination directory that no longer exist in the source directory.
- Detects and allows to automatically repair changes in the metadata of a file preserving the oldest version of it (only applicable if the file has not been modified besides its metadata).
- Allows the application of an exclusion list of directory paths that should not be taken into consideration in the add/update/remove/repair routines.

## Requirements

The tool requires the following libraries to be installed, as well as Python3:

- `argparse`
- `hashlib`
- `os`
- `shutil`
- `sys`

## Usage

The tool may be called in the following way:

`python3 Synchronize [-h] -s SRC -d DST [-a] [-f] [-m] [-v VERBOSE] [-x EXCLUDE]`

With the following arguments:

- `-h`: Displays the help message
- `-s SRC, --src SRC`: SRC directory from where to read the files to backup.
- `-d DST, --dst DST`: DST directory in where to store the files to backup.
- `-x EXCLUDE, --exclude EXCLUDE`: EXCLUDE is a string of different subdirectory paths (using relative addresses) to be excluded. The different paths should be separated by a `?` character. E.g: `-x tests?distribution?source/__temp` would exclude the directories: `tests/`, `distribution/` and `source/__temp`.
- `-a, --apply`: Apply the proposed changes automatically. By default it will only list the changes that need to be done to keep the backup up-to-date. It will ask confirmation before performing the changes.
- `-f, --force`: Disables the request for confirmation before applying the changes.
- `-m, --meta`: Checks the metadata integrity of the files, if two files` metadata are different but the files are identical it will overwrite the newest metadata with the oldest of th two.
- `-v VERBOSE, --verbose VERBOSE`: Specifies the level of verbose to utilize: at level 0 nothing is printed, at level 1 only the proposed changes are printed, at level 2 the entire process is printed. By default is 0. If not `--apply` then the minimum is 1.

I personally recommend checking all the changes that will be performed before accepting/applying those changes. Be careful what you do with this tool, and always check you are using the appropriate source and destination directories.

