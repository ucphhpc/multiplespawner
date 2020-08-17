def import_from_module(module_path, module_name, definition):
    module = __import__(module_path, fromlist=[module_name])
    print(module)
    return getattr(module, definition)
