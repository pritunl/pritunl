library model;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:async' as async;
import 'dart:math' as math;

class Attr {
  final name;
  const Attr(this.name);
}

class Model {
  var _loadCheckId;
  var http;
  var url;
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
        new Duration(milliseconds: 200), () {
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

  Model(ng.Http this.http);

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
    var data = this.parse(responseData);
    var mirror = mirrors.reflect(this);

    data.forEach((key, value) {
      try {
        mirror.setField(new Symbol(key), value);
      } on NoSuchMethodError {
      }
    });
  }

  save() {
  }
}
