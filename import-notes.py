#!/usr/bin/env python

from sys import exit
import subprocess
from pathlib import Path
import inquirer
from inquirer import errors


class Conversion:
    def __init__(self, out_ext, convert_script):
        self.out_ext = out_ext
        self.convert_script = convert_script

    def convert(self, srcs, cwd):
        subprocess.run(self.convert_script + srcs, cwd=cwd)
        return self.out_ext



def at_least_one(_, current_answers):
    if len(current_answers) <= 0:
        raise errors.ValidationError("",
                                     reason="Please select at least one file")
    return True


# Configuration variables
src_dir = "~/downloads/"
notes_parent_dir = "~/school/notes"
src_conversion = {
    ".pptx": Conversion(".pdf", [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
    ]),
    ".pdf": Conversion(".svgz", [
        str(Path(Path(__file__).parent, "./helper/write-templates/pdf2write.sh")),
        "-s",
        "letter",
    ]),
}
final_ext = ".svgz"


# Get paths
src_dir_path = Path(src_dir).expanduser()
src_files = {}
for ext in src_conversion.keys():
    src_files.update({path.name:path for path in src_dir_path.glob("*" + ext)})
note_dirs = {path.name:path for path
             in Path(notes_parent_dir).expanduser().iterdir()
             if path.is_dir()}

if len(src_files) < 1:
    print(f"No source files found within {src_dir}")
    exit(1)


# Get user choice
answer = inquirer.prompt([
    inquirer.Checkbox(
        "selected_srcs",
        message="Select files to import",
        choices=src_files.keys(),
        default=src_files.keys(),
        validate=at_least_one
    ),
    inquirer.List(
        "notes_dir",
        message="Select target dir",
        choices=note_dirs.keys(),
    ),
])

if answer is None:
    exit(0)


# Convert
src_files = {key:src_files[key] for key in answer["selected_srcs"]}
out_files = {path.with_suffix(final_ext):{path} for path in src_files.values()}

while src_files:
    for ext, conversion in src_conversion.items():
        ext_srcs = [name for name, path in src_files.items() if path.suffix == ext]
        if not ext_srcs:
            continue
        out_ext = conversion.convert(ext_srcs, src_dir_path)

        if out_ext != final_ext:
            for src_name in ext_srcs:
                src = src_files[src_name]
                new_src = src.with_suffix(out_ext)
                src_files[new_src.name] = new_src
                out_files[src.with_suffix(final_ext)].add(new_src)

        for src_name in ext_srcs:
            src_files.pop(src_name)


# Move and delete
for out_file, srcs in out_files.items():
    if not out_file.exists():
        print(f"\n{out_file} doesn't exist, something must have when wrong",
              "during the conversion process. Quitting...")
        exit(1)

    for src in srcs:
        src.unlink()

    move_path = Path(note_dirs[answer["notes_dir"]], out_file.name)
    if move_path.exists():
        print(f"\n{str(move_path).replace(str(Path.home()), '~')} already",
              f"exists, leaving converted doc in {src_dir}")
        continue
    out_file.replace(move_path)
