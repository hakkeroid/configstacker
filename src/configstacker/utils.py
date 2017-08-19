# -*- coding: utf-8 -*-

__all__ = ['make_subdicts']


def make_subdicts(base, keychain):
    while keychain:
        subsection = keychain.pop(0)
        base = base.setdefault(subsection, {})
    return base
