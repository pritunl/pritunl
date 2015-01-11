library model;

import 'package:pritunl/exceptions.dart';

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:collection' as collection;
import 'dart:async' as async;
import 'dart:math' as math;

class Collection extends collection.IterableBase {
  var _collection;
  var _loadCheckId;
  var http;
  var url;
  var model;
  var errorStatus;
  var errorData;
  var loading;

  Collection(ng.Http this.http) : _collection = [];

  get iterator {
    return this._collection.iterator;
  }

  fetch() {
    var loadCheckId = new math.Random().nextInt(32000);
    this._loadCheckId = loadCheckId;
    new async.Future.delayed(
      new Duration(milliseconds: 200), () {
        if (this._loadCheckId == loadCheckId) {
          this.loading = true;
        }
      });

    return this.http.get(this.url).then((response) {
      this._loadCheckId = null;
      this.loading = false;
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this._loadCheckId = null;
      this.loading = false;
      this.errorStatus = err.status;
      this.errorData = err.data;
      throw err;
    });
  }

  parse(data) {
    return data;
  }

  import(responseData) {
    var data;

    try {
      data = this.parse(responseData);
    } on IgnoreResponse {
      return;
    }

    var modelCls = mirrors.reflectClass(this.model);
    var initSym = new Symbol('');
    this._collection = [];

    data.forEach((value) {
      var mdl = modelCls.newInstance(initSym, [this.http]).reflectee;
      mdl.import(value);
      this._collection.add(mdl);
    });
  }

  save() {
  }
}
