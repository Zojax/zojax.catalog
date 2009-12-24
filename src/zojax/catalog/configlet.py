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
from zope import interface, event
from zope.component import getUtility, queryUtility
from zope.proxy import removeAllProxies
from zope.app.component.hooks import getSite
from zope.lifecycleevent import ObjectCreatedEvent

from catalog import Catalog
from interfaces import ICatalog, ICatalogConfiglet, ICatalogAwareSite


class CatalogConfiglet(object):
    interface.implements(ICatalogConfiglet)

    @property
    def catalog(self):
        try:
            catalog = getUtility(ICatalog)
        except:
            catalog = self.install()

        return catalog

    def install(self):
        site = getSite()

        while not ICatalogAwareSite.providedBy(site):
            site = getattr(site, '__parent__', None)

            if site is None:
                raise LookupError("Can't find catalog container")

        sm = site.getSiteManager()
        if 'contentCatalog' not in sm:
            catalog = Catalog()
            event.notify(ObjectCreatedEvent(catalog))
            removeAllProxies(sm)['contentCatalog'] = catalog
            sm.registerUtility(sm['contentCatalog'], ICatalog)

        return sm['contentCatalog']

    def isAvailable(self):
        catalog = queryUtility(ICatalog)
        if catalog is None:
            site = getSite()

            while not ICatalogAwareSite.providedBy(site):
                site = getattr(site, '__parent__', None)

                if site is None:
                    return False

        return super(CatalogConfiglet, self).isAvailable()
