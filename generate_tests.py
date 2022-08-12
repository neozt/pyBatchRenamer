import os
from pathlib import Path
import string
import random


TEST_FOLDER = Path(os.getcwd())/Path("tests")


def generate_test_folder1():
    dir = TEST_FOLDER/Path('MyAwesomePhotos')
    dir.mkdir()
    for _ in range(30):
        random_id = (random.choice(string.ascii_uppercase) +
                     ''.join(random.sample(string.digits, 6)))
        filename = f'Image{random_id}.jpg'
        with open(dir/filename, 'w') as f:
            pass


def generate_test_folder2():
    dir = TEST_FOLDER/Path('Notebook')
    dir.mkdir()
    for i in range(1, 15):
        if i == 3 or i == 12:
            continue
        filename = f'my note ({i}).txt'
        with open(dir/filename, 'w') as f:
            pass


def generate_test_folder3():
    dir = TEST_FOLDER/Path('Music')
    dir.mkdir()
    for i in range(25, 53):
        filename = f'My_sound-clip #{i}.mp3'
        with open(dir/filename, 'w') as f:
            pass


def main():
    TEST_FOLDER.mkdir()
    generate_test_folder1()
    generate_test_folder2()
    generate_test_folder3()


if __name__ == '__main__':
    main()
