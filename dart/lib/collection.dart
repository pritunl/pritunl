library collection;

import 'package:pritunl/exceptions.dart';
import 'package:pritunl/model.dart' as mdl;

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
  int errorStatus;
  dynamic errorData;
  bool loadingLong;

  var _loading;
  set loading(bool val) {
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
      this.errorStatus = err.status;
      this.errorData = err.data;
      throw err;
    });
  }

  dynamic parse(dynamic data) {
    return data;
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

    var collection = [];

    data.forEach((value) {
      var mdl = modelCls.newInstance(initSym, [this.http]).reflectee;
      mdl.import(value);
      collection.add(mdl);
    });

    this._collection = collection;

    this.imported();
  }

  void imported() {
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
      this.errorStatus = err.status;
      this.errorData = err.data;
      throw err;
    });
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
