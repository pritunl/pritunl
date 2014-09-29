from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import bson
import json
import os
import copy

class MongoObject(object):
    fields = set()
    fields_default = {}
    fields_required = {}

    def __new__(cls, id=None, doc=None, spec=None, **kwargs):
        mongo_object = object.__new__(cls)
        mongo_object.changed = set()
        mongo_object.id = id

        if id or doc or spec:
            mongo_object.exists = True
            try:
                mongo_object.load(doc=doc, spec=spec)
            except NotFound:
                return None
        else:
            mongo_object.exists = False
            mongo_object.id = str(bson.ObjectId())
        return mongo_object

    def __setattr__(self, name, value):
        if name != 'fields' and name in self.fields:
            self.changed.add(name)
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        if name in self.fields:
            if name in self.fields_default:
                value = self.fields_default[name]
                if isinstance(value, list):
                    value = copy.copy(value)
                    setattr(self, name, value)
                elif isinstance(value, dict):
                    value = value.copy()
                    setattr(self, name, value)
                return value
            return
        raise AttributeError(
            'MongoObject instance has no attribute %r' % name)

    @property
    def _id(self):
        id = self.id
        if len(id) == 24:
            return bson.ObjectId(id)
        return id

    @cached_static_property
    def collection(cls):
        raise TypeError('Database collection must be specified')

    def load(self, doc=None, spec=None):
        if doc and spec:
            raise TypeError('Doc and spec both defined')
        if not doc:
            if not spec:
                spec = {
                    '_id': self._id,
                }
            doc = self.collection.find_one(spec)
            if not doc:
                raise NotFound('Document not found', {
                    'spec': spec,
                })
        doc['id'] = str(doc.pop('_id'))
        for key, value in doc.iteritems():
            setattr(self, key, value)
        self.exists = True
        self.changed = set()

    def export(self):
        doc = self.fields_default.copy()
        doc['_id'] = self._id
        for field in self.fields:
            if hasattr(self, field):
                doc[field] = getattr(self, field)
        return doc

    def get_commit_doc(self, fields=None):
        doc = {}

        if fields:
            if isinstance(fields, basestring):
                fields = (fields,)
        elif self.exists:
            fields = self.fields

        if fields or doc:
            for field in fields:
                doc[field] = getattr(self, field)
        elif not self.exists:
            doc = self.fields_default.copy()
            doc['_id'] = self._id
            for field in self.fields:
                if hasattr(self, field):
                    doc[field] = getattr(self, field)

        if self.exists:
            for field in self.fields_required:
                if doc.get(field, True) is None:
                    raise ValueError('Required %r field is missing' % field)
        else:
            for field in self.fields_required:
                if doc.get(field) is None:
                    raise ValueError('Required %r field is missing' % field)
        return doc

    def commit(self, fields=None, transaction=None):
        doc = self.get_commit_doc(fields=fields)

        if transaction:
            collection = transaction.collection(
                self.collection.name_str)
        else:
            collection = self.collection

        if doc:
            collection.update({
                '_id': self._id,
            }, {
                '$set': doc,
            }, upsert=True)

        self.exists = True
        self.changed = set()

    def remove(self):
        self.collection.remove(self._id)

    def read_file(self, field, path):
        with open(path, 'r') as field_file:
            setattr(self, field, field_file.read())

    def write_file(self, field, path, chmod=None):
        with open(path, 'w') as field_file:
            if chmod:
                os.chmod(path, chmod)
            field_file.write(getattr(self, field))
