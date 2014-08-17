from constants import *
from exceptions import *
import bson
import os

class MongoObject:
    fields = set()
    fields_default = {}

    def __init__(self, id=None, doc=None, spec=None):
        self._changed = set()
        self.id = id

        if id or doc or spec:
            self._exists = True
            self.load(doc=doc, spec=spec)
        else:
            self._exists = False
            self.id = str(bson.ObjectId())

    def __setattr__(self, name, value):
        if name != 'fields' and name in self.fields:
            self._changed.add(name)
        self.__dict__[name] = value

    def __getattr__(self, name):
        if name in self.fields:
            if name not in self.__dict__:
                if name in self.fields_default:
                    return self.fields_default[name]
                return
        elif name not in self.__dict__:
            raise AttributeError(
                'MongoObject instance has no attribute %r' % name)
        return self.__dict__[name]

    @staticmethod
    def get_collection():
        raise TypeError('Database collection must be specified')

    def load(self, doc=None, spec=None):
        if doc and spec:
            raise TypeError('Doc and spec both defined')
        if not doc:
            if not spec:
                spec = {
                    '_id': bson.ObjectId(self.id),
                }
            doc = self.get_collection().find_one(spec)
            if not doc:
                raise NotFound('Document not found', {
                    'spec': spec,
                })
        doc['id'] = str(doc.pop('_id'))
        self.__dict__.update(doc)

    def commit(self, fields=None):
        if fields:
            if isinstance(fields, basestring):
                fields = (fields,)
        elif self._exists:
            fields = self._changed

        if fields:
            doc = {}
            for field in fields:
                doc[field] = self.__dict__[field]
            self.get_collection().update({
                '_id': bson.ObjectId(self.id)
            }, {
                '$set': doc
            }, upsert=True)
        else:
            doc = self.fields_default.copy()
            doc['_id'] = bson.ObjectId(self.id)
            for field in self.fields:
                if field in self.__dict__:
                    doc[field] = self.__dict__[field]
            self.get_collection().save(doc)

    def remove(self):
        self.get_collection().remove(bson.ObjectId(self.id))

    def read_file(self, field, path):
        with open(path, 'r') as field_file:
            setattr(self, field, field_file.read())

    def write_file(self, field, path, chmod=None):
        with open(path, 'w') as field_file:
            if chmod:
                os.chmod(path, chmod)
            field_file.write(getattr(self, field))
