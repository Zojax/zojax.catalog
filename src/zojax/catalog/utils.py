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
from zope.component import getUtility, queryUtility
from zope.proxy import removeAllProxies
from zope.configuration.name import resolve
from zope.security import checkPermission
from zope.security.management import queryInteraction, getSecurityPolicy
from zope.securitypolicy.interfaces import Allow, Deny
from zope.app.security.interfaces import \
    IUnauthenticatedPrincipal, IAuthenticatedGroup, IEveryoneGroup
from zope.app.intid.interfaces import IIntIds
from zojax.security.securitypolicy import SecurityPolicy
from zojax.security.utils import getPrincipal, checkPermissionForPrincipal
from zojax.security.interfaces import \
    IZojaxSecurityPolicy, IPrincipalGroups, IExtendedGrantInfo

from interfaces import ICatalog


class Indexable(object):

    cache = {}

    def __init__(self, name):
        self.name = name

    def __call__(self, content, default=None):
        name = self.name

        if name not in self.cache:
            try:
                self.cache[name] = resolve(name)
            except ImportError:
                self.cache[name] = None

        if name in self.cache:
            adapter = self.cache[name]
            if adapter is not None:
                return adapter(content, default)


def getRequest():
    interaction = queryInteraction()

    if interaction is not None:
        for participation in interaction.participations:
            return participation


def getAccessList(context, permission):
    context = removeAllProxies(context)
    grant = IExtendedGrantInfo(context)

    interaction = queryInteraction()
    if not IZojaxSecurityPolicy.providedBy(interaction):
        interaction = SecurityPolicy()

    allowed = {}
    for role, setting in grant.getRolesForPermission(permission):
        if role == 'content.Owner':
            for principal, setting in grant.getPrincipalsForRole('content.Owner'):
                if setting is Allow and principal:
                    allowed['user:'+principal] = 1

        elif setting is Allow:
            allowed[role] = 1

    for principal, setting in grant.getPrincipalsForPermission(permission):
        if principal:
            uid = 'user:'+principal
            if setting is Allow:
                allowed[uid] = 1
            elif setting is Deny and uid in allowed:
                del allowed[uid]

    roles = []
    for role in allowed.keys():
        if not role.startswith('user:'):
            hasPrincipals = False
            for principal, setting in grant.getPrincipalsForRole(role):
                uid = 'user:'+principal
                if interaction.cached_decision(context,principal,(),permission):
                    allowed[uid] = 1
                    hasPrincipals = True
                elif uid in allowed:
                    del allowed[uid]
            if not hasPrincipals:
                del allowed[role]

    # check special groups
    for grp in (IUnauthenticatedPrincipal, IAuthenticatedGroup, IEveryoneGroup):
        principal = queryUtility(grp)

        if principal is not None:
            uid = 'user:%s'%principal.id

            if checkPermissionForPrincipal(principal, permission, context):
                allowed[uid] = 1
            else:
                if uid in allowed:
                    del allowed[uid]

    return allowed.keys()


def listAllowedRoles(principal, context):
    grant = IExtendedGrantInfo(context)

    result = ['user:%s'%principal.id]
    for role, setting in grant.getRolesForPrincipal(principal.id):
        if setting is Allow:
            result.append(role)

    # fixme: check IGroupInformation
    for group in IPrincipalGroups(principal).getGroups():
        result.append('user:%s'%group.id)

    return result


def indexObject(object):
    ob = removeAllProxies(object)
    id = getUtility(IIntIds).getId(ob)

    for name, catalog in getUtilitiesFor(ICatalog, context=ob):
        catalog.index_doc(id, ob)
