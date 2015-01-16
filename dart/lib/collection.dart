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
  var loadingLong;

  var _loading;
  set loading(val) {
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
  get loading {
    return this._loading;
  }

  Collection(ng.Http this.http) : _collection = [];

  get iterator {
    return this._collection.iterator;
  }

  fetch() {
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
    var initSym = const Symbol('');
    this._collection = [];

    data.forEach((value) {
      var mdl = modelCls.newInstance(initSym, [this.http]).reflectee;
      mdl.import(value);
      this._collection.add(mdl);
    });

    this.imported();
  }

  imported() {
  }

  save() {
  }
}
