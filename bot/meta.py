def exist(obj: dict) -> bool:
    return obj is not None and 'detail' not in obj


def deco(func):
    async def wrapper(*args, **kwargs):
        res = await func(*args, **kwargs)
        if not exist(res):
            res = None
        return res

    return wrapper


class GettersWrapping(type):

    @staticmethod
    def attr_handler(attr_name, attr_value):
        if callable(attr_value) and attr_name.startswith('get_'):
            return deco(attr_value)
        return attr_value

    def __new__(mcs, name, bases, attrs):
        new_attrs = {}
        for attr_name, attr_value in attrs.items():
            new_attrs[attr_name] = mcs.attr_handler(attr_name, attr_value)
        return super().__new__(mcs, name, bases, new_attrs)
