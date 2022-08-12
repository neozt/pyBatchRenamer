from setuptools import setup, find_packages


setup(
    name="pyBatchRenamer",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "inquirer",
        "typer",
    ],
    entry_points={
        'console_scripts': ['neo-renamer=batch_rename:runner']}
)
