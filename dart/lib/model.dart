library model;

import 'package:angular/angular.dart' as ng;
import 'dart:mirrors' as mirrors;

class Model {
  var _http;

  Model(ng.Http this._http);

  get url {
    return '';
  }

  fetch() {
    this._http.get(this.url).then((response) {
      this.import(response.data);
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
