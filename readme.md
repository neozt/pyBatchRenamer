# pyBatchRenamer
#### Command Line Interface used to batch rename files within a folder to a new naming format while preserving original sequence number.

This CLI is created to ease the process of batch renaming multiple files in a folder that share a common naming format, while differing from each other by a certain sequence number. The program extracts this sequence number based on a mask provided by the user (or automatically inferred by the program) and proceeds to rename each file to the desired output format incorporating the same sequence number as the original.

For example, the following renaming can be done easily:
image01.img, image02.img, image03.img -> Hawaii - 1.img, Hawaii - 2.img, Hawaii - 3.img.

![CLI Demo](assets/demo.gif)
___
## How to use
1. Clone the repository
2. `pip install inquirer typer`
3. `python batch_rename.py PARENT_DIR`, where `PARENT_DIR` is the parent folder of the folder that contains the batch files that you want to rename.

This will initiate the CLI, which will take you through the following steps:
  1. Select the target folder.
  2. Optionally rename the target folder (Leave empty to skip this step).
  3. Input the extractor mask used to extract the seq num from the original names, with %s as placeholder for the sequence number.
  4. Input the output format you want the files to be renamed to, again with %s as placeholder for the sequence number.
  5. Inspect the changes and confirm if it is want you wanted. If not, type n and the program will undo all changes made to files and folder names.


#### Alternative for Windows users
A bat script has been included so that the CLI can be run from any directory by running `batch_rename.bat` or simply `batch_rename`. The script will then call the python program, automatically passing in the current working directory as the parent directory.

**Steps to setup the script:**
1. Edit `batch_rename.bat`, changing `"path/to/python.exe" "path/to/batch_rename.py" "%cd%"` to reflect the path to the Python interpreter as well as to the Python script on your machine.
2. Add the parent folder that contains `batch_rename.bat` to your environment `PATH` variable so that it can be called anywhere.
