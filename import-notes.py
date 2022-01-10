#!/usr/bin/env python
import subprocess
import re
from sys import exit, stdout
from pathlib import Path
import inquirer
from inquirer import errors as inquirer_errors

# Configuration variables
source_dir = "~/downloads/"
notes_parent_dir = "~/school/notes"
final_extension = ".svgz"


# Classes
class Converter:
    def __init__(self, input_ext, output_ext):
        self.input_ext = input_ext
        self.output_ext = output_ext

    @staticmethod
    def is_final():
        return False

    def convert(self, filenames, cwd):
        # Should return list of output files
        pass

    def process(self, files):
        matches = [file for file in files if file.suffix == self.input_ext]
        if not matches:
            return []
        # Assumes all files are in the same working directory
        self.convert([file.name for file in matches], matches[0].parent)
        # Assume one-to-one conversion
        expected_out = [file.with_suffix(self.output_ext) for file in matches]
        return [file for file in expected_out if file.exists()]


class PowerPointConverter(Converter):
    def __init__(self):
        super().__init__(".pptx", ".pdf")

    def convert(self, filenames, cwd):
        subprocess.run(
            "soffice --headless --convert-to pdf".split() + filenames,
            cwd=cwd,
        )


class PdfConverter(Converter):
    def __init__(self):
        super().__init__(".pdf", ".svgz")

    @staticmethod
    def is_final():
        return True

    @staticmethod
    def get_pdf_dim(filename, cwd):
        pdfinfo = subprocess.check_output(["pdfinfo", filename], cwd=cwd).decode(stdout.encoding)
        return map(float, re.search(
            r"^\s*Page\s+size:\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)",
            pdfinfo,
            flags=re.MULTILINE
        ).groups())

    @classmethod
    def compute_scale(cls, dpi, filename, cwd):
        width, height = cls.get_pdf_dim(filename, cwd)
        # TODO: Smarter scaling or make PM for writetopdf
        # Match width to letter paper
        return (8.5 * dpi) / width

    def convert(self, filenames, cwd):
        dpi = 96
        for filename in filenames:
            print(f"Converting {filename} to {self.output_ext}...")
            subprocess.run(
                [
                    "pdftowrite",
                    "--dpi", str(dpi),
                    "--scale", f"{self.compute_scale(dpi, filename, cwd):.2f}",
                    filename
                ],
                cwd=cwd,
                stderr=subprocess.DEVNULL
            )


class Sources:
    def __init__(self, dir, converters):
        self.dir = Path(dir).expanduser()
        self.converters = converters
        self.files = sum(
            [list(self.dir.glob("*" + ext)) for ext in
                [converter.input_ext for converter in self.converters]],
            []
        )
        self.converted_files = []

    @property
    def empty(self):
        return len(self.files) == 0

    def get_names(self):
        return [file.name for file in self.files]

    def select(self, names):
        self.files = [file for file in self.files if file.name in names]

    def convert(self):
        for converter in self.converters:
            new_files = converter.process(self.files)
            if converter.is_final():
                self.converted_files += new_files
            else:
                self.files += new_files

    def delete_all(self):
        for file in self.files:
            file.unlink()


class Destination:
    def __init__(self, parent_dir, final_ext):
        self.dir = None
        self.parent_dir = Path(parent_dir).expanduser()
        self.final_ext = final_ext

        self.cleaned_filelist = []
        self.suggestion = None

    def list_options(self):
        return [dir.name for dir in self.parent_dir.iterdir() if dir.is_dir()]

    def select(self, dirname):
        self.dir = Path(self.parent_dir, dirname)
        if not self.dir.exists():
            raise FileNotFoundError
        self.compute_cleaned_filelist()

    def compute_cleaned_filelist(self):
        blacklist = ["midterm", "review"]
        glob = [file.name for file in self.dir.glob("*" + self.final_ext)]
        self.cleaned_filelist = [name for name in glob if not any(sub in name for sub in blacklist)]

    def tail_ls(self):
        if len(self.cleaned_filelist) > 0:
            print("  ".join(self.cleaned_filelist[-3:]))
        else:
            print(f"[No patterned {self.final_ext} files in this directory]")

    def suggest_name(self):
        if len(self.cleaned_filelist) == 0:
            return None

        if self.suggestion is None:
            match = re.fullmatch(fr"(\D*)(\d\d)(\D*)\{self.final_ext}", self.cleaned_filelist[-1])
            if match is None:
                return None
            self.suggestion = list(match.groups(default=""))

        self.suggestion[1] = str(int(self.suggestion[1]) + 1).zfill(2)
        return "".join(self.suggestion)

    def import_files(self, files, renames):
        for file in files:
            dest = Path(
                self.dir,
                Path(renames[file.stem]).with_suffix(file.suffix)
            )
            if dest.exists():
                print(f"\n{str(dest).replace(str(Path.home()), '~')} already",
                      "exists, leaving converted doc")
                continue
            file.replace(dest)


# Helper Functions
def at_least_one(_, current_answers):  # Validation function for inquirer
    if len(current_answers) <= 0:
        raise inquirer_errors.ValidationError("", reason="Please select at least one file")
    return True


if __name__ == "__main__":
    # Setup
    sources = Sources(source_dir, [PowerPointConverter(), PdfConverter()])
    if sources.empty:
        print(f"No source files found within {source_dir}")
        exit(1)

    dest = Destination(notes_parent_dir, final_extension)
    if len(dest.list_options()) == 0:
        print(f"No note directories found within {notes_parent_dir}")
        exit(1)

    # Get user input
    select_ans = inquirer.prompt([
        inquirer.Checkbox(
            "sources",
            message="Select files to import",
            choices=sources.get_names(),
            default=sources.get_names(),
            validate=at_least_one
        ),
        inquirer.List(
            "notes_dir",
            message="Select destination dir",
            choices=dest.list_options(),
        ),
    ])
    if select_ans is None:
        exit(0)
    sources.select(select_ans["sources"])
    dest.select(select_ans["notes_dir"])

    print(f"Existing files in {dest.dir.name}/")
    dest.tail_ls()
    print()
    renames = inquirer.prompt([
        inquirer.Text(
            file.stem,
            message=f"Converted stem for \"{file.name}\"",
            default=dest.suggest_name() or file.stem,
        )
        for file in sources.files
    ])
    if renames is None:
        exit(0)

    # Perform tasks
    print()
    sources.convert()
    dest.import_files(sources.converted_files, renames)
    sources.delete_all()
