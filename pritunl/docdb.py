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

    def _find(self, query, slow=False, only_id=False):
        if 'id' in query:
            doc_id = query['id']
            if only_id:
                self._lock.acquire()
                try:
                    if doc_id in self._docs:
                        return [doc_id]
                    return []
                finally:
                    self._lock.release()
            else:
                doc = self.find_id(doc_id)
                if doc:
                    return [doc]
                return []

        need = len(query)
        possible = {}
        found = []

        self._lock.acquire()
        try:
            index_count = 0
            for index_key in list(self._index.keys()):
                val = query.get(index_key, None)

                if val is not None:
                    query.pop(index_key, None)
                    index_count += 1
                    index = self._index[index_key]
                    if val in index:
                        for doc_id in index[val]:
                            matched = possible.get(doc_id, 0) + 1
                            possible[doc_id] = matched
                            if matched == need:
                                if only_id:
                                    found.append(doc_id)
                                else:
                                    doc = copy.deepcopy(self._docs[doc_id])
                                    doc['id'] = doc_id
                                    found.append(doc)

            if not index_count:
                if not slow:
                    raise IndexError('Non indexed query')

                for doc_id, doc in list(self._docs.items()):
                    match = True
                    for key, val in list(query.items()):
                        if doc[key] != val:
                            match = False
                            break
                    if match:
                        if only_id:
                            found.append(doc_id)
                        else:
                            doc = copy.deepcopy(doc)
                            doc['id'] = doc_id
                            found.append(doc)
            elif index_count != need:
                for doc_id, matched in list(possible.items()):
                    if matched != index_count:
                        continue
                    doc = self._docs[doc_id]
                    match = True
                    for key, val in list(query.items()):
                        if doc[key] != val:
                            match = False
                            break
                    if match:
                        if only_id:
                            found.append(doc_id)
                        else:
                            doc = copy.deepcopy(doc)
                            doc['id'] = doc_id
                            found.append(doc)
        finally:
            self._lock.release()

        return found

    def find_all(self):
        found = []

        for doc_id, doc in list(self._docs.items()):
            doc = copy.deepcopy(doc)
            doc['id'] = doc_id
            found.append(doc)

        return found

    def find(self, query, slow=False):
        return self._find(query, slow)

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

            for index_key, index in list(self._index.items()):
                val = doc.get(index_key)
                if val is not None:
                    index[val].add(doc_id)

            self._docs[doc_id] = doc
        finally:
            self._lock.release()

        return orig_doc

    def _update(self, doc_ids, update):
        for doc_id in doc_ids:
            doc = self._docs[doc_id]

            for key, val in list(update.items()):
                if key in self._indexes:
                    index = self._index[key]

                    cur_val = doc.get(key)
                    if cur_val is not None:
                        val_index = index[cur_val]
                        val_index.remove(doc_id)
                        if len(val_index) == 0:
                            index.pop(cur_val)

                    if val is not None:
                        index[val].add(doc_id)

                doc[key] = val

    def count(self, query, slow=False):
        self._lock.acquire()
        try:
            if not query:
                return len(self._docs)
            doc_ids = self._find(query, slow, True)
        finally:
            self._lock.release()

        return len(doc_ids)

    def count_id(self, doc_id):
        self._lock.acquire()
        try:
            if doc_id in self._docs:
                return 1
        finally:
            self._lock.release()

        return 0

    def update(self, query, update, slow=False):
        self._lock.acquire()
        try:
            doc_ids = self._find(query, slow, True)
            self._update(doc_ids, update)
        finally:
            self._lock.release()

        return len(doc_ids)

    def update_id(self, doc_id, update):
        self._lock.acquire()
        try:
            if doc_id not in self._docs:
                return False
            self._update([doc_id], update)
        finally:
            self._lock.release()

        return True

    def _remove(self, doc_ids):
        for doc_id in doc_ids:
            doc = self._docs.pop(doc_id)

            for index_key, index in list(self._index.items()):
                val = doc.get(index_key)
                if val is not None:
                    val_index = index[val]
                    val_index.remove(doc_id)
                    if len(val_index) == 0:
                        index.pop(val)

    def remove(self, query, slow=False):
        self._lock.acquire()
        try:
            doc_ids = self._find(query, slow, True)
            self._remove(doc_ids)
        finally:
            self._lock.release()

        return len(doc_ids)

    def remove_id(self, doc_id):
        self._lock.acquire()
        try:
            if doc_id not in self._docs:
                return False
            self._remove([doc_id])
        finally:
            self._lock.release()
