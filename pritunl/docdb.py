import threading
import collections
import bson
import copy

class DocDb(object):
    def __init__(self, *indexes):
        self._indexes = set()
        self._index = {}
        self._lock = threading.RLock()
        self._docs = {}

        for ind in indexes:
            self._indexes.add(ind)
            self._index[ind] = collections.defaultdict(set)

    def find(self, query, slow=False):
        if 'id' in query:
            doc = self.find_id(query['id'])
            if doc:
                return [doc]
            return []

        need = len(query)
        possible = collections.defaultdict(set)
        found = []

        self._lock.acquire()
        try:
            index_count = False
            for index_key in self._index.keys():
                val = query.pop(index_key, None)
                if val is not None:
                    index_count += 1
                    index = self._index[index_key]
                    if val in index:
                        for doc_id in index[val]:
                            matched = possible[doc_id]
                            matched.add(index_key)
                            if len(matched) == need:
                                doc = copy.deepcopy(self._docs[doc_id])
                                doc['id'] = doc_id
                                found.append(doc)

            if not index_count:
                if not slow:
                    raise IndexError('Non indexed query')

                for doc_id, doc in self._docs.items():
                    match = True
                    for key, val in query.items():
                        if doc[key] != val:
                            match = False
                            break
                    if match:
                        doc = copy.deepcopy(doc)
                        doc['id'] = doc_id
                        found.append(doc)
            elif index_count != need:
                for doc_id, matched in possible.items():
                    if len(matched) != index_count:
                        continue
                    doc = self._docs[doc_id]
                    match = True
                    for key, val in query.items():
                        if doc[key] != val:
                            match = False
                            break
                    if match:
                        doc = copy.deepcopy(doc)
                        doc['id'] = doc_id
                        found.append(doc)
        finally:
            self._lock.release()

        return found

    def find_id(self, doc_id):
        self._lock.acquire()
        try:
            doc = self._docs.get(doc_id)
            if doc:
                doc = copy.deepcopy(doc)
                doc['id'] = doc_id
                return doc
        finally:
            self._lock.release()

    def insert(self, doc, upsert=False):
        orig_doc = doc
        doc = copy.deepcopy(doc)
        doc_id = doc.pop('id', bson.ObjectId())
        orig_doc['id'] = doc_id

        self._lock.acquire()
        try:
            if upsert:
                self.remove_id(doc_id)
            elif doc_id in self._docs:
                raise KeyError('Doc id already exists')

            for index_key, index in self._index.items():
                val = doc.get(index_key)
                if val is not None:
                    index[val].add(doc_id)

            self._docs[doc_id] = doc
        finally:
            self._lock.release()

        return orig_doc

    def remove(self, doc):
        pass

    def remove_id(self, doc_id):
        self._lock.acquire()
        try:
            doc = self._docs.get(doc_id)
            if not doc:
                return

            for index_key, index in self._index.items():
                val = doc.get(index_key)
                if val is not None:
                    val_index = index[val]
                    val_index.remove(doc_id)
                    if len(val_index) == 0:
                        index.pop(val)

            self._docs.pop(doc_id)
        finally:
            self._lock.release()
