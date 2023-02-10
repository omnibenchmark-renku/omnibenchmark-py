from typing import Union


def into_list(obj: Union[str, list]) -> list:
    if not isinstance(obj, list):
        obj = [obj]
    return obj