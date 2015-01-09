library model;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:collection' as collection;

class Collection extends collection.IterableBase {
  var _collection;
  var http;
  var url;
  var model;
  var errorStatus;
  var errorData;

  Collection(ng.Http this.http);

  get iterator {
    if (this._collection == null) {
      return [].iterator;
    }
    else {
      return this._collection.iterator;
    }
  }

  fetch() {
    return this._http.get(this.url).then((response) {
      this.import(response.data);
      return response.data;
    }).catchError((err) {
      this.errorStatus = err.status;
      this.errorData = err.data;
      throw err;
    });
  }

  parse(data) {
    return data;
  }

  import(responseData) {
    var data = this.parse(responseData);
    var modelCls = mirrors.reflectClass(this.model);
    var initSym = new Symbol('');
    this._collection = [];

    data.forEach((value) {
      var mdl = modelCls.newInstance(initSym, [this._http]).reflectee;
      mdl.import(value);
      this._collection.add(mdl);
    });
  }

  save() {
  }
}
