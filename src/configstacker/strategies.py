# -*- coding: utf-8 -*-


def add(previous, next_):
    if previous is None:
        return next_
    return previous + next_


def collect(previous, next_):
    if previous is None:
        return [next_]
    return previous + [next_]


def merge(previous, next_):
    return add(previous, next_)
