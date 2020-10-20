def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def import_klass(module_path, klass_name):
    return import_from_module(module_path, "module", klass_name)


def make(klass_module_path, *args, **kwargs):
    _klass_module_path = klass_module_path.split(".")
    klass = import_klass(".".join(_klass_module_path[:-1]), _klass_module_path[-1])
    return klass(*args, **kwargs)


def recursive_format(input, value):
    if isinstance(input, list):
        for item_index, item_value in enumerate(input):
            if isinstance(item_value, str):
                try:
                    input[item_index] = item_value.format(**value)
                except KeyError:
                    continue
            recursive_format(item_value, value)
    if isinstance(input, dict):
        for input_key, input_value in input.items():
            if isinstance(input_value, str):
                try:
                    input[input_key] = input_value.format(**value)
                except KeyError:
                    continue
            recursive_format(input_value, value)
    if hasattr(input, "__dict__"):
        recursive_format(input.__dict__, value)
