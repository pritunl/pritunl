library collection;

import 'package:pritunl/exceptions.dart';
import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/event.dart' as evnt;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:collection' as collection;
import 'dart:async' as async;
import 'dart:math' as math;

abstract class Collection extends collection.IterableBase {
  List<mdl.Model> _collection;
  int _loadCheckId;
  ng.Http http;
  String url;
  Type model;
  String error;
  String errorMsg;
  int errorStatus;
  bool loadingLong;
  Function onImport;
  Function onAdd;
  Function onChange;
  Function onRemove;
  evnt.Listener listener;

  var _loading;
  void set loading(bool val) {
    if (val) {
      var loadCheckId = new math.Random().nextInt(32000);
      this._loadCheckId = loadCheckId;
      this._loading = true;

      new async.Future.delayed(
        const Duration(milliseconds: 200), () {
          if (this._loadCheckId == loadCheckId) {
            this.loadingLong = true;
          }
        });
    }
    else {
      this._loadCheckId = null;
      this.loadingLong = false;
      this._loading = false;
    }
  }
  bool get loading {
    return this._loading;
  }

  String get eventType {
    throw new UnimplementedError();
  }

  String get eventResource {
    return null;
  }

  Collection(this.http) : _collection = [];

  Iterator get iterator {
    return this._collection.iterator;
  }

  int get length {
    return this._collection.length;
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

  async.Future fetch() {
    this.loading = true;

    return this.http.get(this.url).then((response) {
      this.loading = false;
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.loading = false;
      return new async.Future.error(this.parseError(err));
    }, test: (e) => e is ng.HttpResponse);
  }

  dynamic parse(dynamic data) {
    return data;
  }

  dynamic parseError(dynamic err) {
    var httpErr = new HttpError(err);

    this.error = httpErr.error;
    this.errorMsg = httpErr.errorMsg;
    this.errorStatus = httpErr.resp.status;

    return httpErr;
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

  void clearError() {
    this.error = null;
    this.errorMsg = null;
    this.errorStatus = null;
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

  void imported() {
  }

  void added(mdl.Model model) {
  }

  void changed(mdl.Model model) {
  }

  void removed(mdl.Model model) {
  }

  dynamic _send(String method, List<String> fields) {
    var data = [];
    var mirror = mirrors.reflect(this);
    var methodFunc;

    this.loading = true;

    for (var model in this._collection) {
      data.add(model.export(fields));
    }

    if (method == 'post') {
      methodFunc = this.http.post;
    }
    else if (method == 'put') {
      methodFunc = this.http.put;
    }
    else {
      throw new ArgumentError('Unkown method');
    }

    return methodFunc(this.url, data).then((response) {
      this.loading = false;
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.loading = false;
      return new async.Future.error(this.parseError(err));
    }, test: (e) => e is ng.HttpResponse);
  }

  dynamic save([List<String> fields]) {
    return this._send('put', fields);
  }

  dynamic create([List<String> fields]) {
    return this._send('post', fields);
  }

  void clear() {
    this._collection = [];
  }
}
