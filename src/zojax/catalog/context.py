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
from zope.component import getUtility
from zope.proxy import removeAllProxies
from zope.app.intid.interfaces import IIntIds
from zope.app.component.interfaces import ISite

from interfaces import ISearchContext


def getSearchContext(contexts, all=True):
    values = []
    ids = getUtility(IIntIds)

    if type(contexts) not in (tuple, list):
        contexts = (contexts,)

    for context in contexts:
        if isinstance(context, int):
            values.append(context)
        else:
            while context is not None:
                sContext = ISearchContext(context, None)
                if sContext is not None:
                    id = ids.queryId(removeAllProxies(sContext))
                    if id is not None:
                        values.append(id)
                        if not all:
                            break

                context = getattr(context, '__parent__', None)

    return values


@component.adapter(ISite)
@interface.implementer(ISearchContext)
def siteSearchContext(site):
    return site


class SearchContext(object):

    def __init__(self, context, default=None):
        self.searchContext = getSearchContext(context.__parent__)
