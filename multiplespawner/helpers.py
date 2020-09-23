def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def import_klass(module_path, klass_name):
    return import_from_module(module_path, "module", klass_name)


def make(klass_module_path, *args, **kwargs):
    _klass_module_path = klass_module_path.split(".")
    klass = import_klass(".".join(_klass_module_path[:-1]), _klass_module_path[-1])
    return klass(*args, **kwargs)
