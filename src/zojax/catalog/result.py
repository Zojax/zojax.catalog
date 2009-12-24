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
import sys, types
from BTrees.IFBTree import weightedIntersection

minValue = float(-sys.maxint-1)


class ResultSet(object):
    """Lazily accessed set of objects."""

    def __init__(self, uids, uidutil):
        self.uids = uids
        self.uidutil = uidutil

        try:
            self.uids_keys = uids.keys()
        except:
            self.uids_keys = uids

        self._len = len(self.uids_keys)
        self._objects = {}

    def __len__(self):
        return self._len

    def __iter__(self):
        for uid in self.uids:
            obj = self.uidutil.getObject(uid)
            yield obj

    def __nonzero__(self):
        return bool(self.uids)

    def __getitem__(self, idx):
        if isinstance(idx, types.SliceType):
            values = []
            objects = self._objects

            length = self._len

            start = idx.start or 0
            if (-start) > length:
                start = 0
            stop = idx.stop or length
            if stop > length:
                stop = length

            for idx in range(start, stop):
                if idx in objects:
                    values.append(objects[idx])
                else:
                    values.append(self[idx])
            return values

        try:
            return self._objects[idx]
        except KeyError:
            uid = self.uids_keys[idx]
            ob = self.uidutil.getObject(uid)
            self._objects[idx] = ob
            return ob

    def get(self, idx, default=None):
        try:
            return self[idx]
        except IndexError:
            return default

    def items(self):
        for uid in self.uids:
            obj = self.uidutil.getObject(uid)
            yield uid, obj

    def applySorting(self, index=None):
        if index is not None:
            _t, res = weightedIntersection(self.uids, index)
        else:
            res = self.uids
        self.uids = [id for weight, id in res.byValue(minValue)]
        self.uids_keys = self.uids
        self._len = len(self.uids)


class ReverseResultSet(ResultSet):

    def __iter__(self):
        for idx in range(len(self.uids)):
            yield self[idx]

    def __getitem__(self, idx):
        if isinstance(idx, types.SliceType):
            length = self._len

            start = idx.start or 0
            if (-start) > length:
                start = 0
            stop = idx.stop or length
            if stop > length:
                stop = length

            getitem = self.__getitem__
            return [getitem(idx) for idx in range(start, stop)]

        if idx < 0:
            idx = - idx - 1
        else:
            idx = self._len - idx - 1

        if idx < 0:
            raise IndexError('list index out of range')

        return super(ReverseResultSet, self).__getitem__(idx)

    def items(self):
        uids = self.uids
        for idx in range(len(uids)):
            yield uids[idx], self[idx]
