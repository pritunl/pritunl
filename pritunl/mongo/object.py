from pritunl.exceptions import *
from pritunl.helpers import *

import os
import copy

class MongoObject(object):
    fields = set()
    fields_default = {}
    fields_required = {}

    def __new__(cls, id=None, doc=None, spec=None, fields=None,
            upsert=False, **kwargs):
        from pritunl import utils
        fields = fields or cls.fields

        mongo_object = object.__new__(cls)
        mongo_object.changed = set()
        mongo_object.unseted = set()
        mongo_object.id = id
        mongo_object.loaded_fields = fields

        if id or doc or spec:
            mongo_object.exists = True
            try:
                mongo_object.load(doc=doc, spec=spec, fields=fields)
            except NotFound:
                if not upsert:
                    return None
                mongo_object.exists = False
                if not id:
                    mongo_object.id = utils.ObjectId()
        else:
            mongo_object.exists = False
            mongo_object.id = utils.ObjectId()
        return mongo_object

    def __setattr__(self, name, value):
        if name != 'fields' and name in self.fields:
            self.changed.add(name)
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        if name in self.fields:
            if name not in self.loaded_fields:
                raise ValueError('Cannot get unloaded field %r' % name)
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

    @cached_static_property
    def collection(cls):
        raise TypeError('Database collection must be specified')

    def load(self, doc=None, spec=None, fields=None):
        if doc and spec:
            raise TypeError('Doc and spec both defined')
        if not doc:
            if not spec:
                spec = {
                    '_id': self.id,
                }
            if fields:
                doc = self.collection.find_one(spec, list(fields))
            else:
                doc = self.collection.find_one(spec)
            if not doc:
                raise NotFound('Document not found', {
                    'spec': spec,
                })
        doc['id'] = doc.pop('_id')
        self.__dict__.update(doc)
        self.exists = True
        self.changed = set()

    def export(self):
        doc = self.fields_default.copy()
        doc['_id'] = self.id
        for field in self.fields:
            if hasattr(self, field):
                doc[field] = getattr(self, field)
        return doc

    def get_commit_doc(self, fields=None):
        doc = {}

        if fields is not None:
            if isinstance(fields, str):
                fields = (fields,)
        elif self.exists:
            fields = self.fields

        if fields or doc:
            for field in fields:
                doc[field] = getattr(self, field)
        elif not self.exists:
            doc = self.fields_default.copy()
            doc['_id'] = self.id
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

    def unset(self, field):
        self.unseted.add(field)

    def commit(self, fields=None, transaction=None, spec=None):
        doc = self.get_commit_doc(fields=fields)
        unset = {x: '' for x in self.unseted}
        response = False

        if transaction:
            collection = transaction.collection(
                self.collection.name_str)
        else:
            collection = self.collection

        if doc or unset:
            update_doc = {}

            if spec is None:
                spec = {
                    '_id': self.id,
                }

            if doc:
                for field in self.unseted:
                    doc.pop(field, None)
                update_doc['$set'] = doc

            if unset:
                update_doc['$unset'] = unset

            response = collection.update(
                spec, update_doc, upsert=True)

            if transaction:
                response = True
            else:
                response = response['updatedExisting']

        self.exists = True
        self.changed = set()
        self.unseted = set()

        return response

    def remove(self):
        self.collection.remove(self.id)

    def read_file(self, field, path, rstrip=True):
        with open(path, 'r') as field_file:
            file_data = field_file.read()
            if rstrip:
                file_data = file_data.rstrip('\n')
            setattr(self, field, file_data)

    def write_file(self, field, path, chmod=None):
        with open(path, 'w') as field_file:
            if chmod:
                os.chmod(path, chmod)
            field_file.write(getattr(self, field))
