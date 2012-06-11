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
"""Catalog Views

$Id$
"""
import logging

from zope.index.interfaces import IStatistics
from zope.proxy import removeAllProxies
from zojax.catalog.interfaces import _
from zojax.statusmessage.interfaces import IStatusMessage

logger = logging.getLogger('zojax.catalog')


class Advanced(object):

    def update(self):
        request = self.request
        catalog = self.context.catalog

        if 'form.button.remove' in request:
            idx = request.get('indexIds', ())
            if not idx:
                IStatusMessage(request).add(_('Please select indexes.'))
            else:
                for indexId in idx:
                    if indexId in catalog:
                        del catalog[indexId]
                IStatusMessage(request).add(
                    _('Catalog indexes have been removed.'))

        if 'form.button.reindex' in request:
            logger.info('Clearing catalog...')
            catalog.clear()
            logger.info('Clearing catalog done!')
            logger.info('Updating indexes...')
            catalog.updateIndexes()
            logger.info('Updating indexes done!')
            IStatusMessage(self.request).add(_('Catalog has been reindexed.'))

        if 'form.button.security' in self.request:
            logger.info('Updating security indexes...')
            catalog.updateIndexesByName(
                ('allowedRoleAndPrincipals',
                 'draftSubmitTo', 'draftPublishTo', 'draftPublishable'))
            logger.info('Updating security indexes done!')
            IStatusMessage(self.request).add(_('Catalog has been reindexed.'))

        self.catalog = catalog

    def getIndexInfo(self, id):
        index = removeAllProxies(self.catalog[id])
        if IStatistics.providedBy(index):
            return {'documents': index.documentCount, 'words': index.wordCount}
        return {'documents': '--', 'words': '--'}
