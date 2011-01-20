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
from pytz import utc
from datetime import datetime

from zope.component import getUtility, getUtilitiesFor
from zope.dublincore.interfaces import IDCTimes, IDCPublishing, IDCExtended
from zope.dublincore.interfaces import IDCDescriptiveProperties
from zope.index.text.interfaces import ISearchableText
from zope.app.catalog.text import TextIndex
from zope.app.security.interfaces import IAuthentication

from zc.catalog.catalogindex import SetIndex, ValueIndex

from zojax.security.interfaces import IPrincipalGroups
from zojax.content.type.interfaces import IContentType, IContentTypeType, IItem

from index import DateTimeValueIndex, PathIndex
from utils import Indexable
from context import getSearchContext
from interfaces import IHiddenContent


def traversablePathIndex():
    return PathIndex()


def nameIndex():
    return ValueIndex('__name__')


def titleIndex():
    return ValueIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableTitle'))


def ownersIndex():
    return SetIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableOwners'))


def hiddenIndex():
    return ValueIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableHidden'))


def createdIndex():
    return DateTimeValueIndex('created', IDCTimes, resolution=4)


def modifiedIndex():
    return DateTimeValueIndex('modified', IDCTimes, resolution=4)


def expiresIndex():
    return DateTimeValueIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableExpires'),
        resolution=4)


def effectiveIndex():
    return DateTimeValueIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableEffective'),
        resolution=4)


def creatorsIndex():
    return SetIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableCreators'))


def typeIndex():
    return ValueIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableContentType'))


def typeTypeIndex():
    return SetIndex(
        'value', Indexable('zojax.catalog.defaultindexes.IndexableContentTypeType'))


def searchContextIndex():
    return SetIndex(
        'searchContext',
        Indexable('zojax.catalog.context.SearchContext'))


def allowedRoleAndPrincipalsIndex():
    return SetIndex(
        'allowed',
        Indexable('zojax.catalog.securityinfo.IndexableSecurityInformation'))


def searchableTextIndex():
    return TextIndex('getSearchableText', ISearchableText, True)


class IndexableTitle(object):

    def __init__(self, content, default=None):
        item = IItem(content, None)
        props = IDCDescriptiveProperties(content, None)
        if props is None:
            if item is None:
                self.value = default
            else:
                self.value = item.title.lower()
        else:
            self.value = props.title.lower()
            if not self.value and item is not None:
                self.value = item.title.lower()


class IndexableContentType(object):

    def __init__(self, content, default=None):
        tp = IContentType(content, None)
        if tp is None:
            self.value = default
        else:
            self.value = tp.name

        self.type = self.value


class IndexableContentTypeType(object):

    def __init__(self, content, default=None):
        ct = IContentType(content, None)
        if ct is None:
            self.value = default
        else:
            types = []
            for name, ctt in getUtilitiesFor(IContentTypeType):
                if ctt.providedBy(ct):
                    types.append(name)
            self.value = types

        self.typeType = self.value


class IndexableHidden(object):

    def __init__(self, content, default=None):
        self.value = IHiddenContent.providedBy(content)


class IndexableOwners(object):

    value = ()

    def __init__(self, content, default=None):
        groups = IPrincipalGroups(content, None)
        if groups is None:
            return

        owners = {}
        for group in groups.getGroups():
            owners[group.id] = 1

        owners[groups.principal.id] = 1
        self.value = owners.keys()
        self.owners = self.value


class IndexableCreators(object):

    def __init__(self, content, default=None):
        extended = IDCExtended(content, None)
        if extended is None:
            self.value = default
            self.creators = default
            return

        principals = {}
        getPrincipal = getUtility(IAuthentication).getPrincipal

        for creator in extended.creators:
            try:
                principal = getPrincipal(creator)

                groups = IPrincipalGroups(principal, None)
                if groups is None:
                    continue

                for group in groups.getGroups():
                    principals[group.id] = 1

                principals[groups.principal.id] = 1
            except:
                pass

        self.value = principals.keys()
        self.creators = self.value


class IndexableExpires(object):

    value = datetime(2100, 1, 1, tzinfo=utc)

    def __init__(self, content, default=None):
        publishing = IDCPublishing(content, None)

        if publishing is not None:
            expires = publishing.expires
            if expires is not None and expires < self.value:
                self.value = expires


class IndexableEffective(object):

    value = datetime(2000, 1, 1, tzinfo=utc)

    def __init__(self, content, default=None):
        publishing = IDCPublishing(content, None)

        if publishing is not None:
            effective = publishing.effective
            if effective is not None and effective >= self.value:
                self.value = effective
