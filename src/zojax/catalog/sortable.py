##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id$
"""
from zope import interface, component
from BTrees.OOBTree import OOBTree, OOSet
from zc.catalog.interfaces import IValueIndex
from zc.catalog.interfaces import INormalizationWrapper

from interfaces import ISortable


class ValueIndexSortable(object):
    interface.implements(ISortable)

    def __init__(self, index):
        self.index = index

    def sort(self, result):
        index = self.index
        values = self.index.documents_to_values

        seq = OOBTree()
        for key in result:
            idx = values.get(key, None)
            if idx is None:
                continue

            data = seq.get(idx, None)
            if data is None:
                data = OOSet()
            data.insert(key)
            seq[idx] = data

        result = []
        for idx, data in seq.items():
            result.extend(data)

        return result


@component.adapter(IValueIndex)
@interface.implementer(ISortable)
def valueSortable(index):
    if INormalizationWrapper.providedBy(index):
        if IValueIndex.providedBy(index.index):
            return ValueIndexSortable(index.index)
    elif IValueIndex.providedBy(index):
        return ValueIndexSortable(index)
