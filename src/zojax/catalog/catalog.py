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
""" catalog implementation

$Id$
"""
from pytz import utc
from threading import local
from datetime import datetime
from BTrees.IFBTree import IFBTree, weightedIntersection

from zope import interface, event, component
from zope.proxy import removeAllProxies, sameProxiedObjects
from zope.component import getUtility, queryUtility, getUtilitiesFor
from zope.interface.common.idatetime import ITZInfo
from zope.datetime import parseDatetimetz
from zope.lifecycleevent import ObjectCreatedEvent
from zope.security.management import queryInteraction
from zope.app.catalog import catalog
from zope.app.component.hooks import getSite, setSite
from zope.app.component.interfaces import ISite
from zope.app.intid.interfaces import IIntIds
from zope.app.security.interfaces import IUnauthenticatedPrincipal

from zojax.cacheheaders.interfaces import IAfterCallEvent
from zojax.content.type.interfaces import IDraftedContent, ISearchableContent

import interfaces, patch
from interfaces import _, ICatalog, ICatalogConfiglet, \
    ICatalogIndexFactory, ISortable, ISearchContext

from context import getSearchContext
from utils import getRequest, listAllowedRoles
from result import ResultSet, ReverseResultSet

import logging
logger = logging.getLogger("zojax.catalog")

class Catalog(catalog.Catalog):
    interface.implements(ICatalog)

    optimize_index = False

    def createIndex(self, name, factory):
        index = factory()
        event.notify(ObjectCreatedEvent(index))
        self[name] = index

        return self[name]

    def getIndex(self, indexId):
        if indexId in self:
            return self[indexId]

        factory = queryUtility(ICatalogIndexFactory, indexId)
        if factory is not None:
            return self.createIndex(indexId, factory)

    def getIndexes(self):
        names = []

        for index in self.values():
            names.append(removeAllProxies(index.__name__))
            yield index

        for name, indexFactory in getUtilitiesFor(ICatalogIndexFactory):
            if name not in names:
                yield self.createIndex(name, indexFactory)

    def clear(self):
        for index in self.getIndexes():
            index.clear()

    def index_doc(self, docid, texts):
        texts = ISearchableContent(texts, None)
        if texts is None:
            return

        if self.optimize_index:
            request = getRequest()
            if request is not None and \
                    getattr(request, 'publication', None) is not None:
                localData.add(self, docid, texts)
                return

        self._index_doc(docid, texts)

    def _index_doc(self, docid, texts):
        for index in self.getIndexes():
            if IDraftedContent.providedBy(texts) and \
                    index.__name__ in ('searchableText',):
                continue

            index.index_doc(docid, texts)

    def unindex_doc(self, docid):
        for index in self.getIndexes():
            index.unindex_doc(docid)

    def updateIndex(self, index):
        logger.info('Starting updating of `%s` index' % index.__name__)
        for uid, obj in self._visitSublocations():
            obj = ISearchableContent(obj, None)
            if obj is None:
                continue

            index.index_doc(uid, obj)
        logger.info('Done updating of `%s` index' % index.__name__)

    def updateIndexes(self):
        logger.info('Starting updateIndexes')
        indexes = list(self.getIndexes())

        for uid, obj in self._visitSublocations():
            obj = ISearchableContent(obj, None)
            if obj is None:
                continue

            logger.info('updateIndexes for `%s`' % obj)
            for index in indexes:
                #logger.info('Reindex of `%s` object' % index.__name__)
                index.index_doc(uid, obj)

        logger.info('Done updateIndexes')

    def updateIndexesByName(self, indexes):
        for id in indexes:
            index = self.getIndex(id)
            if index is not None:
                self.updateIndex(index)

    def updateIndexesByQuery(self, indexNames=[], searchContext=None,
                             noPublishing=False, noSecurityChecks=False,
                             indexes=None, **searchterms):
        uidutil = getUtility(IIntIds)
        results = self.searchResults(
            searchContext=searchContext,
            noPublishing=noPublishing, noSecurityChecks=noSecurityChecks,
            indexes=indexes, **searchterms)

        if results:
            indexes = []
            if indexNames:
                for name in indexNames:
                    indexes.append(self.getIndex(name))
            else:
                indexes = self.getIndexes()

            for obj in results:
                for index in indexes:
                    index.index_doc(uidutil.getId(obj), obj)

    def apply(self, query, sort_on=None, indexes=None):
        results = []
        for index_name, index_query in query.items():
            if indexes and index_name in indexes:
                index = indexes[index_name]
            else:
                index = self.getIndex(index_name)

            if index is None:
                continue

            r = index.apply(index_query)

            if r is None:
                continue
            if not r:
                # empty results
                return r
            results.append((len(r), r))

        if not results:
            # no applicable indexes, so catalog was not applicable
            return None

        results.sort() # order from smallest to largest
        _t, result = results.pop(0)

        for _t, r in results:
            _t, result = weightedIntersection(result, r)

        # sort result by index
        if sort_on:
            sort_index = self.getIndex(sort_on)
            if sort_index is not None:
                sortable = ISortable(sort_index, None)
                if sortable is None:
                    raise interfaces.NotSortableIndex(
                        _("Index doesn't support sorting."))
                result = sortable.sort(result)
            else:
                raise interfaces.InvalidIndex(
                    _('Invalid index: ${sort_on}', mapping={'sort_on':sort_on}))

        return result

    def searchResults(self, sort_on=None, sort_order=None, searchContext=None,
                      noPublishing=False, noSecurityChecks=False,
                      showHidden=False, indexes=None,
                      _max_expires=datetime(2199, 1, 1, tzinfo=utc),
                      _min_effective=datetime(1999, 12, 31, tzinfo=utc),
                      **searchterms):

        # publishing info
        if not noPublishing:
            tz = ITZInfo(getRequest(), utc)
            value = datetime.now(tz)
            now = datetime(
                value.year, value.month, value.day, value.hour,
                value.minute, value.second, value.microsecond, tz)

            if 'expires' not in searchterms:
                searchterms['expires'] = {'between': (now, _max_expires)}
            if 'effective' not in searchterms:
                searchterms['effective'] = {'between': (_min_effective, now)}

        # security info
        if not noSecurityChecks:
            request = getRequest()
            if request is not None:
                if searchContext is not None:
                    users = listAllowedRoles(request.principal, searchContext)
                else:
                    users = listAllowedRoles(request.principal, getSite())

                searchterms['allowedRoleAndPrincipals'] = {'any_of': users}

        # hidden
        if 'hidden' not in searchterms:
            if showHidden:
                searchterms['hidden'] = {'any_of': (True, False)}
            else:
                searchterms['hidden'] = {'any_of': (False,)}

        # search context
        if searchContext is None:
            searchContext = getSite()

        if isinstance(searchContext, dict):
            searchterms['searchContext'] = searchContext
        else:
            context = getSearchContext(searchContext, False)
            if context:
                searchterms['searchContext'] = {'any_of': context}

        #apply pluggable query
        searchterms.update(self.getPluggableQuery())

        # apply
        results = self.apply(searchterms, sort_on, indexes)

        if results is None:
            results = IFBTree()

        uidutil = getUtility(IIntIds)
        if sort_order == 'reverse':
            return ReverseResultSet(results, uidutil)
        else:
            return ResultSet(results, uidutil)

    def getPluggableQuery(self):
        query = {}
        for name, utility in sorted(getUtilitiesFor(interfaces.ICatalogQueryPlugin),
                                    key=lambda x: x[1].weight):
            if utility.isAvailable():
                query.update(utility())
        return query


def queryCatalog(sort_on=None, sort_order=None, **searchterms):
    return getUtility(ICatalogConfiglet).catalog.searchResults(
        sort_on, sort_order, **searchterms)


class LocalData(local):

    objects = None

    def add(self, catalog, docid, ob):
        if self.objects is None:
            self.objects = []

        item = (catalog, docid, ob)
        if item not in self.objects:
            self.objects.append(item)

    def reindex(self):
        if not self.objects:
            return

        ids = getUtility(IIntIds)

        for catalog, docid, ob in self.objects:
            id = ids.queryId(ob)
            if id == docid:
                catalog._index_doc(id, ob)

        self.objects = []


localData = LocalData()

@component.adapter(IAfterCallEvent)
def afterCallHandler(event):
    localData.reindex()
