"""CLI used to batch rename files while preserving sequence number.

The original files should have similar formatting to each other, with the only
differing part being the sequence number. 

This program will attempt to rename every file in the chosen folder by extracting 
the sequence number out from the original names based on an input mask (extractor)
provided by the user (or automatically inferred by the program) and then combining
the extracted seq num with the user provided template to generate the target name.

Run using: python batch_rename.py PARENT_DIR
    where PARENT_DIR is the PARENT folder of the folder that contains the batch files
    that we wish the rename. 
"""
from pathlib import Path
import re

import inquirer
import typer

DEFAULT_FORMAT_TEMPLATE = '{folder} - %s'


app = typer.Typer()


@app.command()
def main(
    path: Path,
    direct: bool = typer.Option(
        False,
        '--direct', '-d',
        help="Directly use path as target_dir instead of as parent_dir."
    )
):
    """Batch rename files. If --direct is used, PATH will point directly to the
    folder containing the files to be renamed. Otherwise, PATH points at the parent
    directory whose folders can then be selected as the target folder."""

    # Input: folder to rename
    target_folder: Path = None
    if not direct:
        selected_folder = inquirer.list_input(
            "Select folder to rename",
            choices=[f.name for f in path.iterdir() if f.is_dir()]
        )
        target_folder = path/selected_folder
    else:
        target_folder = path

    # Find all files in selected folder and display to user.
    files: list[Path] = [f for f in target_folder.iterdir() if f.is_file()]
    if not files:
        print(f"No files found in {target_folder}. Exiting...")
        typer.Exit()
    print(f'Found {len(files)} files in {target_folder}.')
    display_files(files)

    # Input: Rename folder to new name (Optional)
    new_folder_name = inquirer.text(
        "[Optional] Rename target folder",
        default=None
    )
    old_folder_name = target_folder
    if new_folder_name:
        try:
            new_path = target_folder.with_name(new_folder_name)
            target_folder = target_folder.rename(new_path)
            print(
                f'Folder successfully renamed: {old_folder_name.name} -> {target_folder.name}\n')
        except OSError as e:
            print(
                f'Could not rename folder {old_folder_name!r} -> {new_path!r}. {e!r}')
            undo(old_folder_name, target_folder)
            typer.Abort()

        files = [f for f in target_folder.iterdir() if f.is_file()]

    # Input: Extractor used to extract id from original file name.
    input_extractor = prompt_extractor(default=guess_extractor(files))
    extractor = extractor_regex(input_extractor)

    # Get input: Desired output file name format.
    try:
        fmt = prompt_format(default=guess_format(target_folder.name))
    except ValueError as e:
        print(e)
        undo(old_folder_name, target_folder)
        typer.Abort()

    # Determine padding required (for sequence numbers that are numeric)
    ids = []
    for f in files:
        try:
            ids.append(extract_id(f.stem, extractor))
        except ValueError as e:
            print(e)
            undo(old_folder_name, target_folder)
            typer.Abort()
    pad_to = 0
    if all((is_float(id) for id in ids)):
        str_lengths = (len(str(int(float(id)))) for id in ids)
        pad_to = max(str_lengths)

    # Sort only if sequence numbers are numeric.
    if all((is_float(id) for id in ids)):
        files.sort(key=lambda x: float(extract_id(x.stem, extractor)))

    # Rename files
    new_files: list[Path] = []
    for file in files:
        new_name = fmt.format(id=extract_id(
            file.stem, extractor).zfill(pad_to))
        new_path = file.with_stem(new_name)
        try:
            new_path = file.rename(new_path)
            new_files.append(new_path)
        except OSError as e:
            print(f'Could not rename {file!r} -> {new_path!r}. {e!r}')
            typer.Abort()

    print(f'{len(new_files)} files in {target_folder.name} has been successfully renamed.')
    changes = [f'{old.name} -> {new.name}'
               for old, new in zip(files, new_files)]
    print(*changes, sep='\n')

    # Prompt for undo.
    confirm = inquirer.confirm('Confirm changes (n to undo changes)',
                               default=True)
    if not confirm:
        undo(old_folder_name, target_folder, files, new_files)
        print('Files and folders have been renamed back to their original names')
    else:
        print('Have a nice day')


def display_files(files: list[Path]):
    file_names = [f.stem for f in files]
    if len(files) < 30:
        print(*file_names, sep='\n')
    else:
        print(*file_names[:10], sep='\n')
        print('...')
        print(*file_names[-5:], sep='\n')
    print('')


def prompt_extractor(default: str = None) -> str:
    print('Enter original name format, with the sequence number portion replaced with %s. Do no include file format (Eg: .txt, .mkv)')
    extractor = inquirer.text(message='Original name format',
                              default=default)
    print('')
    return extractor


def guess_extractor(files: list[Path]) -> str:
    """Guess extractor based on positions of numbers in the first file."""
    first_file = files[0].stem
    # Find all numbers
    matches = list(re.finditer('([\d][\d\.]*)', first_file))
    if not matches:
        return ''
    # We guess that the right-most smallest number is the sequence number.
    match = min(reversed(matches), key=lambda x: float(x.group()))
    start, end = match.span()
    return first_file[:start] + '%s' + first_file[end:]


def extractor_regex(extractor: str) -> str:
    """Return a sanitised regex used for extracting the sequence number.

    Creates a regex that can be used to match a string sequence to extract the 
    desired value at the position mark with (.*). Also sanitises the input by 
    escaping special regex characters.
    For example, 'file name - %s.abc' -> 'file\\ name\\ \\-\\ (.*)\\.abc'.
    """
    # Sanitise the string
    extractor = re.escape(extractor)

    # Replace placeholder with regex matcher
    extractor = extractor.replace('%s', '(.*)')

    return extractor


def extract_id(filename: str, extractor: str) -> str:
    match = re.search(extractor, filename)
    if not match:
        raise ValueError(
            f'Could not extract id from {filename!r} using extractor {extractor!r}')
    return match.group(1)


def guess_format(folder_name: str) -> str:
    """Guess format based on name of folder."""
    return DEFAULT_FORMAT_TEMPLATE.format(folder=folder_name)


def prompt_format(default: str) -> str:
    print('Enter output name format, with %s used as placeholder for sequence number. '
          'Do not include file format (Eg: .txt, .mkv).')
    extractor = inquirer.text(
        message='Output name format',
        default=default
    )
    print('')
    if '{' in extractor or '}' in extractor:
        raise ValueError(
            'Output name format cannot contain characters { or }.')
    return extractor.replace('%s', '{id}')


def undo(old_folder: Path, new_folder: Path, old_files: list[Path] = [], new_files: list[Path] = []):
    """Rename all files and folder back to original name."""
    for old, new in zip(old_files, new_files):
        new.rename(old)

    new_folder.rename(old_folder)


def is_float(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False

    return True


if __name__ == '__main__':
    typer.run(main)
