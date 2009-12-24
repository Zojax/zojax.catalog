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
from zope.app.catalog import catalog
from zc.catalog.index import ValueIndex, SetIndex


def reindexDocSubscriber(event):
    from zope.proxy import removeAllProxies

    ob = removeAllProxies(event.object)
    if INoAutoReindex.providedBy(ob):
        return

    ids = component.queryUtility(IIntIds)
    if ids is None:
        return

    id = ids.queryId(ob)
    if id is None:
        return

    for name, catalog in component.getUtilitiesFor(ICatalog, context=ob):
        catalog.index_doc(id, ob)


catalog.reindexDocSubscriber.func_code = reindexDocSubscriber.func_code


# Below is the patch to workaround a possible bug in BTrees code. This bug
# may cause an error when object is removed and unindexed.
# This patch applies to ValueIndex and SetIndex. It re-initializes
# values_to_documents attribute in case if values_to_documents.get(value)
# returns None (AttributeError) or if docs.remove(doc_id) raises KeyError

def value_index_doc(self, doc_id, value):
    if value is None:
        self.unindex_doc(doc_id)
    else:
        values_to_documents = self.values_to_documents
        documents_to_values = self.documents_to_values
        old = documents_to_values.get(doc_id)
        documents_to_values[doc_id] = value
        if old is None:
            self.documentCount.change(1)
        elif old != value:
            docs = values_to_documents.get(old)

            # Patch begins here
            try:
                docs.remove(doc_id)
            except (AttributeError, KeyError):
                new_values_to_documents = self.family.OO.BTree()
                new_values_to_documents.update(values_to_documents)
                self.values_to_documents = new_values_to_documents
                values_to_documents = self.values_to_documents
                docs = values_to_documents.get(value)
                try:
                    docs.remove(doc_id)
                except AttributeError:
                    docs = True
            # Patch ends here

            if not docs:
                del values_to_documents[old]
                self.wordCount.change(-1)
        self._add_value(doc_id, value)


ValueIndex.index_doc = value_index_doc


def value_unindex_doc(self, doc_id):
    documents_to_values = self.documents_to_values
    value = documents_to_values.get(doc_id)
    if value is not None:
        values_to_documents = self.values_to_documents
        self.documentCount.change(-1)
        del documents_to_values[doc_id]
        docs = values_to_documents.get(value)

        # Patch begins here
        try:
            docs.remove(doc_id)
        except (AttributeError, KeyError):
            new_values_to_documents = self.family.OO.BTree()
            new_values_to_documents.update(values_to_documents)
            self.values_to_documents = new_values_to_documents
            values_to_documents = self.values_to_documents
            docs = values_to_documents.get(value)
            docs.remove(doc_id)
        # Patch ends here

        if not docs:
            del values_to_documents[value]
            self.wordCount.change(-1)


ValueIndex.unindex_doc = value_unindex_doc


def set_unindex_doc(self, doc_id):
    documents_to_values = self.documents_to_values
    values = documents_to_values.get(doc_id)
    if values is not None:
        values_to_documents = self.values_to_documents
        self.documentCount.change(-1)
        del documents_to_values[doc_id]
        for v in values:
            docs = values_to_documents.get(v)

            # Patch begins here
            try:
                docs.remove(doc_id)
            except (AttributeError, KeyError):
                new_values_to_documents = self.family.OO.BTree()
                new_values_to_documents.update(values_to_documents)
                self.values_to_documents = new_values_to_documents
                values_to_documents = self.values_to_documents
                docs = values_to_documents.get(v)
                docs.remove(doc_id)
            # Patch ends here

            if not docs:
                del values_to_documents[v]
                self.wordCount.change(-1)


SetIndex.unindex_doc = set_unindex_doc
