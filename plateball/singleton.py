#! /usr/bin/env python3.5
# Copyright 2017 Gavin Hurlbut
# vim:ts=4:sw=4:ai:et:si:sts=4

class _Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# noinspection PyMissingConstructor
class Singleton(_Singleton('SingletonMeta', (object,), {})):
    def __init__(self):
        pass


def removeSingleton(cls):
    # noinspection PyProtectedMember
    cls._instances.pop(cls, None)

