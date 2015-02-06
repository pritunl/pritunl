library exceptions;

import 'package:angular/angular.dart' as ng;
import 'dart:convert' as convert;

class IgnoreResponse extends Error {
  IgnoreResponse();
}

class HttpError extends Error {
  static var _JSON_START = new RegExp(r'^\s*(\[|\{[^\{])');
  static var _JSON_END = new RegExp(r'[\}\]]\s*$');
  static var _PROTECTION_PREFIX = new RegExp('^\\)\\]\\}\',?\\n');

  ng.HttpResponse resp;
  String error;
  String errorMsg;

  HttpError(ng.HttpResponse err) {
    if (err.data is String) {
      var data = err.data.replaceFirst(_PROTECTION_PREFIX, '');
      if (data.contains(_JSON_START) && data.contains(_JSON_END)) {
        data = convert.JSON.decode(data);
      }

      this.resp = new ng.HttpResponse.copy(err, data: data);

      if (data is Map) {
        this.error = data['error'];
        this.errorMsg = data['error_msg'];
      }
    }
    else {
      this.resp = err;
    }
  }

  String toString() {
    if (this.errorMsg != null) {
      return this.errorMsg;
    }
    return this.resp.toString();
  }
}
