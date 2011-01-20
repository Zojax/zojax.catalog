#############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""indexes, as might be found in zope.index

$Id$
"""
import pytz
import datetime
import zope.interface
from zope.component import getUtility
from zope.proxy import removeAllProxies
from zope.app.intid.interfaces import IIntIds
from zope.traversing.api import getParents

import zc.catalog
from zc.catalog.i18n import _

from zojax.pathindex.index import PathIndex
from zojax.content.shortcut.interfaces import IShortcuts


class DateTimeNormalizer(zc.catalog.index.DateTimeNormalizer):

    def value(self, value):
        if not isinstance(value, datetime.datetime):
            raise ValueError(
                _('This index only indexes timezone-aware datetimes.'))

        if value.tzinfo is None:
            value = datetime.datetime(
                value.year, value.month, value.day, value.hour,
                value.minute, value.second, value.microsecond, pytz.utc)

        value = value.astimezone(pytz.utc)
        return super(DateTimeNormalizer, self).value(value)


@zope.interface.implementer(
    zope.interface.implementedBy(zc.catalog.catalogindex.NormalizationWrapper),
    zc.catalog.interfaces.IValueIndex)
def DateTimeValueIndex(
    field_name=None, interface=None, field_callable=False,
    resolution=2): # hour; good for per-day searches
    ix = zc.catalog.catalogindex.NormalizationWrapper(
        field_name, interface, field_callable, zc.catalog.index.ValueIndex(),
        DateTimeNormalizer(resolution), False)
    zope.interface.directlyProvides(ix, zc.catalog.interfaces.IValueIndex)
    return ix


@zope.interface.implementer(
    zope.interface.implementedBy(zc.catalog.catalogindex.NormalizationWrapper),
    zc.catalog.interfaces.ISetIndex)
def DateTimeSetIndex(
    field_name=None, interface=None, field_callable=False,
    resolution=2): # hour; good for per-day searches
    ix = zc.catalog.catalogindex.NormalizationWrapper(
        field_name, interface, field_callable, zc.catalog.index.SetIndex(),
        DateTimeNormalizer(resolution), True)
    zope.interface.directlyProvides(ix, zc.catalog.interfaces.ISetIndex)
    return ix


class PathIndex(PathIndex):
    
    def _get_values(self, value, includeValue=False):
        try:
            intid = getUtility(IIntIds)
            parents = getParents(value)
        except:
            return None

        if includeValue:
            parents.append(value)
            
        for ob in list(parents):
            parents.extend(IShortcuts(ob, {}).items())

        ids = []
        for ob in parents:
            id = intid.queryId(removeAllProxies(ob))
            if id is not None:
                ids.append(id)

        if ids:
            return ids
        else:
            return None