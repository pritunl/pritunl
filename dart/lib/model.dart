library model;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;
import 'dart:async' as async;
import 'dart:math' as math;

class Model {
  var _loadCheckId;
  var http;
  var url;
  var errorStatus;
  var errorData;
  var loading;

  Model(ng.Http this.http);

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
