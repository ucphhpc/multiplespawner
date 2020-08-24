def import_from_module(module_path, module_name, func_name):
    module = __import__(module_path, fromlist=[module_name])
    return getattr(module, func_name)


def import_klass(module_path, klass_name):
    return import_from_module(module_path, "module", klass_name)
