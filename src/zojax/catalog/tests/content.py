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
from zope import interface
from zojax.content.type.interfaces import IItem
from zojax.content.type.item import PersistentItem
from zojax.content.type.container import ContentContainer
from zojax.content.type.interfaces import ISearchableContent


class IContent(IItem, ISearchableContent):
    """ """

class IFolder(IItem):
    """ """


class Content(PersistentItem):
    interface.implements(IContent)

    def __repr__(self):
        return '<MyContent "%s"-"%s">'%(self.__name__, self.title)


class Folder(ContentContainer):
    interface.implements(IFolder)



class IsSet(object):
    def __init__(self, context, default=False):
        self.isSet = getattr(context, '_set', False)
