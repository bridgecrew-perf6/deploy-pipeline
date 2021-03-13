import os


def with_full_path(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundException(f'Invalid Path: {path}')

    return os.path.realpath(path)


class FileNotFoundException(Exception):
    pass
