

"""

Find and delete Altium history, preview, log and temporary files.

Scans the Altium folder (default: ./Altium next to this script) and all
subfolders. Runs as a dry run by default; pass --delete to remove files.

    python clean_altium.py                # list what would be removed
    python clean_altium.py --delete       # remove it
    python clean_altium.py --outputs      # also include "Project Outputs for *"
    python clean_altium.py PATH --delete  # clean another folder
"""

import  argparse
import  fnmatch
import  shutil
import  sys
from    pathlib     import Path

# Directory names removed with everything inside them.
DIR_PATTERNS = [
                    "History"               ,
                    "__Previews"            ,
                    "Project Logs for *"    ,
                    "Altium Temp"           ,
                ]

# Only removed with --outputs.
OUTPUT_DIR_PATTERNS = [
                    "Project Outputs for *" ,
                ]

# File names removed wherever they appear.
FILE_PATTERNS = [
                    "*.$$$"                 ,   # Altium autosave
                    "*.~*"                  ,   # backup copies
                    "~$*"                   ,   # Office lock files
                    "*.bak"                 ,
                    "*.lck"                 ,
                    "*.log"                 ,
                    "*.tmp"                 ,
                    "*.ldb"                 ,   # Access lock (DB.mdb)
                    "*.laccdb"              ,
                    "*.SchDocPreview"       ,
                    "*.SchDotPreview"       ,
                    "*.PcbDocPreview"       ,
                    "desktop.ini"           ,
                    "Thumbs.db"             ,
                ]

UNITS = ("B", "KB", "MB", "GB")


def matches(name, patterns):
    name = name.lower()
    return any(fnmatch.fnmatchcase(name, p.lower()) for p in patterns)


def find_targets(root, dir_patterns):
    """Return (dirs, files) to remove. Files inside a matched dir are not listed."""
    dirs, files = [], []
    stack       = [root]

    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError as exc:
            print(f"  ! cannot read {current}: {exc}", file=sys.stderr)
            continue

        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if matches(entry.name, dir_patterns):
                    dirs.append(entry)
                else:
                    stack.append(entry)
            elif matches(entry.name, FILE_PATTERNS):
                files.append(entry)

    return sorted(dirs), sorted(files)


def dir_size(path):
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def human(size):
    for unit in UNITS:
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def remove(path, remover):
    try:
        remover(path)
        return True
    except OSError as exc:
        print(f"  ! {path}: {exc}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("root"      , nargs="?"          , type=Path ,
                        default     = Path(__file__).resolve().parent / "Altium",
                        help        = "folder to clean (default: ./Altium)")
    parser.add_argument("--delete"  , action="store_true",
                        help        = "actually delete (default is a dry run)")
    parser.add_argument("--outputs" , action="store_true",
                        help        = 'also remove "Project Outputs for *" folders')
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        sys.exit(f"Not a folder: {root}")

    dir_patterns    = DIR_PATTERNS + (OUTPUT_DIR_PATTERNS if args.outputs else [])
    dirs, files     = find_targets(root, dir_patterns)

    if not dirs and not files:
        print(f"Nothing to clean in {root}")
        return

    total = 0
    for d in dirs:
        size    = dir_size(d)
        total  += size
        print(f"  [dir]  {d.relative_to(root)}  ({human(size)})")
    for f in files:
        size    = f.stat().st_size
        total  += size
        print(f"  [file] {f.relative_to(root)}  ({human(size)})")
    print(f"\n{len(dirs)} folders, {len(files)} files, {human(total)} in {root}")

    if not args.delete:
        print("Dry run. Re-run with --delete to remove them.")
        return

    removed  = sum(remove(d, shutil.rmtree) for d in dirs)
    removed += sum(remove(f, Path.unlink  ) for f in files)
    failed   = len(dirs) + len(files) - removed

    print(f"Removed {removed} items" + (f", {failed} failed (file open in Altium?)" if failed else ""))


if __name__ == "__main__":
    main()
