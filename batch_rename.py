"""CLI used to batch rename files while preserving sequence number.

The original files should have similar formatting to each other, with the only
differing part being the sequence number.

This program will attempt to rename every file in the chosen folder by extracting
the sequence number out from the original names based on an input mask (extractor)
provided by the user (or automatically inferred by the program) and then combining
the extracted seq num with the user provided template to generate the target name.

Build by running python setup develop. Help can be found by running neo-renamer --help.
"""
from inquirer.errors import ValidationError
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
    """
    Batch rename files. If --direct is used, PATH will point directly to the
    folder containing the files to be renamed. Otherwise, PATH points at the parent
    directory whose folders can then be selected as the target folder.
    """

    # Get target_folder.
    path = path.resolve()
    target_folder: Path = None
    if direct:
        # PATH points directly to target_folder.
        target_folder = path
    else:
        # PATH points to parent directory of target_folder.
        # Prompt user to manually select target_folder from the folders within PATH.
        selected_folder = inquirer.list_input(
            "Select folder to rename",
            choices=[f.name for f in path.iterdir() if f.is_dir()]
        )
        target_folder = path/selected_folder

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
        new_folder = old_folder_name.with_name(new_folder_name)
        err = rename_folder(target_folder, new_folder)
        if not err:
            print(
                f'Folder successfully renamed: {old_folder_name.name} -> {target_folder.name}\n')
            target_folder = new_folder
            files = [f for f in target_folder.iterdir() if f.is_file()]
        else:
            print(
                f'Could not rename folder {old_folder_name!r} -> {new_folder!r}. {err!r}')
            undo_renames(old_folder_name, target_folder)
            typer.Abort()

    # Input: Extractor used to extract id from original file name.
    extractor = prompt_extractor(files)

    # Seq nums can either be all numeric or not
    ids = [extract_id(f.stem, extractor) for f in files]
    if all(is_numeric(id) for id in ids):
        # Padding for all seq nums so that they will be equal length.
        padding = max_int_len(ids)
        # Sort based on seq nums for user convenience.
        files.sort(key=lambda x: float(extract_id(x.stem, extractor)))
    else:
        padding = 0

    # Get input: Desired output file name template.
    output_template = prompt_template(
        default=guess_template(target_folder.name))

    # Rename files
    new_files = rename_files(files, extractor, output_template, padding)
    print(f'{len(new_files)} files in {target_folder.name} has been successfully renamed.')
    changes = [f'{old.name} -> {new.name}'
               for old, new in zip(files, new_files)]
    print(*changes, sep='\n')

    # Prompt for undo.
    confirm = inquirer.confirm(
        'Confirm changes (n to undo changes)',
        default=True
    )
    if not confirm:
        undo_renames(old_folder_name, target_folder, files, new_files)
        print('Files and folders have been renamed back to their original names')
    else:
        print('Completed! Have a nice day.')


def display_files(files: list[Path]):
    file_names = [f.stem for f in files]
    if len(files) < 30:
        print(*file_names, sep='\n')
    else:
        print(*file_names[:10], sep='\n')
        print('...')
        print(*file_names[-5:], sep='\n')
    print('')


def prompt_extractor(files) -> str:
    def validate_extractor(answers: dict, current: str) -> bool:
        """Check that a seq num can be extracted from every file in files."""
        extractor = extractor_regex(current)
        for f in files:
            try:
                extract_id(f.stem, extractor)
            except ValueError as e:
                raise ValidationError(
                    '',
                    reason=('Could not extract id from file "{}" '
                            'using extractor <{}>'.format(f.stem, current))
                )
        return True

    print('Enter original name format, with the sequence number portion replaced with %s. '
          'Do not include file format (Eg: .txt, .mkv)')
    extractor = inquirer.text(
        message='Original name format',
        default=guess_extractor(files),
        validate=validate_extractor
    )
    return extractor_regex(extractor)


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


def guess_template(folder_name: str) -> str:
    """Guess format based on name of folder."""
    return DEFAULT_FORMAT_TEMPLATE.format(folder=folder_name)


def prompt_template(default: str) -> str:
    def validate(answers: dict, current: str) -> bool:
        if '{' in current or '}' in current:
            # Inquirer internall calls .format when displaying reason,
            # so we need to escape { and } characters.
            raise ValidationError(
                '', reason='Output format cannot contain {{ or }}')
        return True

    print('Enter output name template, with %s used as placeholder for sequence number. '
          'Do not include file format (Eg: .txt, .mkv).')
    fmt = inquirer.text(
        message='Output name format',
        default=default,
        validate=validate
    )
    return fmt.replace('%s', '{id}')


def undo_renames(old_folder: Path, new_folder: Path, old_files: list[Path] = [], new_files: list[Path] = []):
    """Rename all files and folder back to original name."""
    for old, new in zip(old_files, new_files):
        new.rename(old)

    new_folder.rename(old_folder)


def is_numeric(s: str) -> bool:
    """Return True if s can be converted into a float."""
    try:
        float(s)
    except ValueError:
        return False

    return True


def max_int_len(numbers: list[float | int]) -> int:
    """Determine the length of the largest number in numbers when represented as a string,
    after converting every number into int."""
    return len(str(max(int(n) for n in numbers)))


def validate_extractor(extractor: str, files: list[Path]) -> bool:
    """Validate that extractor can be used to extract a valid seq num
    from all files in files.
    """
    for f in files:
        try:
            extract_id(f.stem, extractor)
        except ValueError:
            return False
    return True


def rename_files(files: list[Path], extractor: str, output_template: str, padding: int) -> list[Path]:
    """Rename files in files according to output_template, based on seq_num extracted from
    original name using extractor. Returns a list of the renamed path instances in the
    same order as the original files."""
    new_files = []
    for file in files:
        seq_num = extract_id(file.stem, extractor).zfill(padding)
        new_name = output_template.format(id=seq_num)
        new_path = file.with_stem(new_name)
        try:
            new_path = file.rename(new_path)
            new_files.append(new_path)
        except OSError as e:
            print(f'Could not rename {file!r} -> {new_path!r}. {e!r}')
            typer.Abort()
    return new_files


def rename_folder(folder: Path, new_folder: Path) -> str | None:
    """Renames folder to new_name and returns the error message if the operation was not succesful."""
    try:
        new_folder = folder.rename(new_folder)
    except OSError as e:
        return str(e)


if __name__ == '__main__':
    typer.run(main)
