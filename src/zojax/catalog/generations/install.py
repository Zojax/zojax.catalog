##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
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
from zope.app.component.interfaces import ISite
from zope.app.zopeappgenerations import getRootFolder
from zope.app.component.site import setSite
from zc.catalog.catalogindex import NormalizationWrapper


def evolve(context):
    root = getRootFolder(context)

    for site in findObjectsMatching(root, ISite.providedBy):
        setSite(site)
        def matchIndex(ob):
            return ob.__class__ in (NormalizationWrapper, )
        try:
            for rt in (site.getSiteManager(), site):
                for index in findObjectsMatching(rt, matchIndex):
                    del index.__parent__[index.__name__]
        finally:
            setSite(None)


def findObjectsMatching(root, condition):
    if condition(root):
        yield root

    if hasattr(root, 'values') and callable(root.values):
        for subobj in root.values():
            for match in findObjectsMatching(subobj, condition):
                yield match
