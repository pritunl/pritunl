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

    for (var i = 0; i < data.length; i++) {
      if (i < this._collection.length) {
        this._collection[i].import(data[i]);
        this.changed(this._collection[i]);
        if (this.onChange != null) {
          this.onChange(this._collection[i]);
        }
      }
      else {
        var mdl = modelCls.newInstance(initSym, [this.http]).reflectee;
        mdl.import(data[i]);
        this._collection.add(mdl);
        this.added(mdl);
        if (this.onAdd != null) {
          this.onAdd(mdl);
        }
      }
    }

    var diff = this._collection.length - data.length;

    if (diff > 0) {
      for (var i = 0; i < diff; i++) {
        var mdl = this._collection.removeLast();
        this.removed(mdl);
        if (this.onRemove != null) {
          this.onRemove(mdl);
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
