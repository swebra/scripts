# Scripts
A collection of quick and dirty QOL scripts which automate some of my daily workflow. They are built for me and me only, expect some messy code and poor documentation.

## `fix-stylus.sh`
Bash script to reset my stylus + touch screen mapping when I connect my laptop to an external display.

## `import-notes.py`
Python script to take downloaded PDFs and PowerPoint files, convert them as needed to a target format (`.svgz` for use in [Stylus Labs Write](http://www.styluslabs.com) in my case), and move them to an appropriate folder. Calls other CLI programs/scripts for most of the conversion, and uses [inquirer](https://pypi.org/project/inquirer/) for pretty user input.
