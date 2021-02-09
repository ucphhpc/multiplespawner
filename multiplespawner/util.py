import os


def makedirs(path):
    try:
        os.makedirs(path)
        return True
    except Exception as err:
        print("Failed to create directory path: {} - {}".format(path, err))
    return False


def write(path, content, mode="w", mkdirs=False, handler=None):
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path) and mkdirs:
        if not makedirs(dir_path):
            return False
    try:
        with open(path, mode) as fh:
            if handler:
                handler.dump(content, fh)
            else:
                fh.write(content)
        return True
    except Exception as err:
        print("Failed to save file: {} - {}".format(path, err))
    return False


def load(path, mode="r", readlines=False, handler=None):
    try:
        with open(path, mode) as fh:
            if handler:
                return handler.load(fh)
            if readlines:
                return fh.readlines()
            return fh.read()
    except Exception as err:
        print("Failed to load file: {} - {}".format(path, err))
    return False


def remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as err:
        print("Failed to remove file: {} - {}".format(path, err))
    return False
