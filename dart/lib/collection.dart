library collection;

import 'package:pritunl/exceptions.dart';
import 'package:pritunl/remote.dart' as remote;
import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/event.dart' as evnt;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:collection' as collection;

abstract class Collection extends remote.Remote with collection.IterableMixin {
  List<mdl.Model> _collection;
  Function onAdd;
  Function onChange;
  Function onRemove;
  Type model;

  Collection(ng.Http http) : super(http), _collection = [];

  Iterator get iterator {
    return this._collection.iterator;
  }

  dynamic operator [](int index) {
    return this._collection[index];
  }

  void add(Map<String, dynamic> attrs) {
    var modelCls = mirrors.reflectClass(this.model);
    var initSym = const Symbol('');
    var mdl = modelCls.newInstance(initSym, [this.http]).reflectee;

    mdl.import(attrs);

    this._collection.add(mdl);
  }

  void validate(String name) {
    for (var model in this) {
      model.validate(name);
    }
  }

  Collection clone() {
    var mirror = mirrors.reflect(this);
    var clone = mirror.type.newInstance(
      const Symbol(''), [this.http]).reflectee;

    for (var model in this) {
      clone._collection.add(model.clone());
    }

    return clone;
  }

  void eventRegister(Function listener) {
    this.listener = evnt.register(listener,
      this.eventType, this.eventResource);
  }

  void eventDeregister() {
    this.listener.deregister();
  }

  void eventUpdate() {
    if (this.listener != null) {
      this.listener.update(this.eventType, this.eventResource);
    }
  }

  void imported() {
  }

  void added(mdl.Model model) {
  }

  void changed(mdl.Model model) {
  }

  void removed(mdl.Model model) {
  }

  void import(dynamic responseData) {
    var data;

    try {
      data = this.parse(responseData);
    } on IgnoreResponse {
      return;
    }

    var modelCls = mirrors.reflectClass(this.model);
    var initSym = const Symbol('');

    var curIds = [];
    var newIds = new Set();
    var models = {};
    var recModels = new collection.Queue();
    var coll = [];
    var links;

    if (this._collection.length != 0) {
      links = this._collection[0].links;
    }

    for (var model in this._collection) {
      curIds.add(model.id);
      models[model.id] = model;
    }

    for (var i = 0; i < data.length; i++) {
      newIds.add(data[i]['id']);
    }

    curIds.forEach((id) {
      if (!newIds.contains(id)) {
        var model = models.remove(id);

        this.removed(model);
        if (this.onRemove != null) {
          this.onRemove(model);
        }

        recModels.add(model);
      }
    });

    for (var i = 0; i < data.length; i++) {
      var added;
      var model = models[data[i]['id']];

      if (model == null) {
        added = true;
        if (recModels.length > 0) {
          model = recModels.removeFirst();

          if (links != null) {
            var mirror = mirrors.reflect(model);

            for (var linkSym in links) {
              mirror.setField(linkSym, null);
            }
          }
        }
        else {
          model = modelCls.newInstance(initSym, [this.http]).reflectee;

        }
      }

      model.import(data[i]);
      coll.add(model);

      if (added == true) {
        this.added(model);
        if (this.onAdd != null) {
          this.onAdd(model);
        }
      }
    }

    if (this.onImport != null) {
      this.onImport(this._collection);
    }

    this.imported();
  }

  void clear() {
    this._collection = [];
  }
}
