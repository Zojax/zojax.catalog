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
""" zojax.catalog interfaces

$Id$
"""
from zope import interface
from zope.index.interfaces import IIndexSearch
from zope.app.catalog.interfaces import ICatalog
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('zojax.catalog')


class CatalogExeception(Exception):
    """ catalog exeption """


class InvalidIndex(CatalogExeception):
    """ invalid index """


class NotSortableIndex(CatalogExeception):
    """Index doesn't support sorting"""


class ISortable(interface.Interface):
    """ sort search result by index """

    def sort(result):
        """ sort apply result """


class ICatalog(ICatalog):

    def getIndex(id):
        """ return index """

    def getIndexes():
        """ return all indexex """

    def updateIndexesByName(indexes):
        """ if indexes is not None, use it as list of requierd indexes """

    def updateIndexesByQuery(indexs=None, **searchterms):
        """ update indexes onfy for results of search """

    def searchResults(sort_on=None, sort_order=None, searchContext=None,
                      noPublishing=False, noSecurityChecks=False,
                      showHidden=False, indexes=None, **searchterms):
        """ search on the given indexes. """


class ISearchContext(interface.Interface):
    """ marker interface for search query context """


class IHiddenContent(interface.Interface):
    """ hidden content """


class ICatalogIndexFactory(interface.Interface):
    """ Categog index factory """

    def __call__():
        """ create index """


class IPortalCatalogProduct(interface.Interface):
    """ portal catalog product """


class ICatalogConfiglet(interface.Interface):
    """ catalog configlet """

    catalog = interface.Attribute('ICatalog object')

    def install():
        """ install catalog """

    def uninstall():
        """ uninstall catalog """


class ICatalogAwareSite(interface.Interface):
    """ marker interface for site that can contain catalog """
