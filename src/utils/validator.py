class SchemaError(Exception):
    pass


def require_keys(data, keys, path):
    missing = [k for k in keys if k not in data]
    if missing:
        raise SchemaError(f"Schema salah di {path}: key hilang: {missing}")
