# -*- coding: utf-8 -*-

__all__ = ['make_subdicts']


def make_subdicts(base, keychain):
    for key in keychain:
        base = base.setdefault(key, {})
    return base
