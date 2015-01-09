library model;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;

class Model {
  var http;
  var url;
  var errorStatus;
  var errorData;

  Model(ng.Http this.http);

  fetch() {
    return this.http.get(this.url).then((response) {
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
