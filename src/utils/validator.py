from src.core.constants import CONDITION_OPERATORS


class SchemaError(Exception):
    pass


def require_keys(data, keys, path):
    missing = [k for k in keys if k not in data]
    if missing:
        raise SchemaError(f"Schema salah di {path}: key hilang: {missing}")


def validate_condition(condition, path):
    require_keys(condition, ["kind"], path)
    operator = condition.get("operator", "EQ")
    if operator not in CONDITION_OPERATORS:
        raise SchemaError(f"Schema salah di {path}: operator tidak dikenal: {operator}")
