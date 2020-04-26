
def load_from_path(function_path):
    parts = function_path.split('.')
    resource = __import__(".".join(parts[:-1]))
    for part in parts[1:]:
        resource = getattr(resource, part)
    return resource

def get_fullname(o):
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__
    return module + '.' + o.__class__.__name__