# neo-renamer
#### Command Line Interface used to batch rename files within a folder to a new naming format while preserving original sequence number.

This CLI was built using the Typer library in Python to ease the process of batch renaming multiple files in a folder that share a common naming format, while differing from each other by a certain sequence number. The program extracts this sequence number based on a mask provided by the user (or automatically inferred by the program) and proceeds to rename each file to the desired output format incorporating the same sequence number as the original.

For example, the following renaming can be done easily:
image01.img, image02.img, image03.img -> Hawaii - 1.img, Hawaii - 2.img, Hawaii - 3.img.

![CLI Demo](assets/demo.gif)
___
## How to use
This project supports building using setuptools. The steps are simple:
1. Clone the repository
2. Run `python setup.py develop`

Now, `neo-renamer PATH` can be called from anywhere. Also supports relative paths, eg: `neo-renamer .`, `neo-renamer ..`, `neo-renamer .\tests`, etc. 
Additionally, it supports the `--direct` flag, which causes the program to treat the input `PATH` argument directly as the target folder, instead of the parent folder that we need to select the target folder from, effectively allowing us to skip the first selection step.

Additional info is available by running `neo-renamer --help` command.
```
>>> neo-renamer --help
Usage: neo-renamer [OPTIONS] PATH

  Batch rename files. If --direct is used, PATH will point directly to the
  folder containing the files to be renamed. Otherwise, PATH points at the
  parent directory whose folders can then be selected as the target folder.

Arguments:
  PATH  [required]

Options:
  -d, --direct                    Directly use path as target_dir instead of
                                  as parent_dir.
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.
```

___
**Note: This CLI was only tested on my machine running Windows 10 with Python 3.10 installed. Use at your own risk.**
