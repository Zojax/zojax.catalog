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
import logging

import transaction
from zope import event, component, interface
from zope.lifecycleevent import ObjectCreatedEvent
from zope.traversing.interfaces import IContainmentRoot
from zope.app.component.hooks import getSite, setSite
from zope.app.appsetup.bootstrap import getInformationFromEvent
from zope.app.appsetup.interfaces import IDatabaseOpenedEvent
from zope.app.appsetup.interfaces import DatabaseOpenedWithRoot
from zope.app.publication.zopepublication import ZopePublication
from zojax.controlpanel.interfaces import IConfiglet

logger = logging.getLogger('zojax.catalog')


@component.adapter(IDatabaseOpenedEvent)
def bootstrapSubscriber(ev):
    db, connection, root, portal = getInformationFromEvent(ev)
    if portal is None:
        connection.close()
        return
    setSite(portal)
    try:
        try:
            catalog = component.getUtility(IConfiglet, 'system.catalog').catalog
        except LookupError:
            return
        if len(list(catalog)) != len(list(catalog.getIndexes())):
            logger.info('Updating Catalog Indexes...')
            catalog.clear()
            catalog.updateIndexes()
            logger.info('Done!')
    finally:
        transaction.commit()
        setSite(None)
        connection.close()
