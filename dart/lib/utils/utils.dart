library utils;

import 'package:angular/angular.dart' as ng;
import 'package:angular/introspection.dart' as introspection;
import 'dart:html' as dom;
import 'dart:convert' as convert;

 dynamic getDirective(dom.Node node, [var type]) {
  while (node != null) {
    var probe = introspection.elementExpando[node];

    if (probe != null) {
      var directives = probe.directives;
      if (directives.length > 0) {
        if (type != null) {
          for (var directive in directives) {
            if (directive.runtimeType == type) {
              return directive;
            }
          }
        }
        else {
          return directives[0];
        }
      }
      return null;
    }

    if (node is dom.ShadowRoot) {
      node = (node as dom.ShadowRoot).host;
    }
    else {
      node = node.parentNode;
    }
  }
  return null;
}

String getDomain() {
  return '${dom.window.location.protocol}//${dom.window.location.host}';
}

class HttpError {
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
      this.error = data['error'];
      this.errorMsg = data['error_msg'];
    }
    else {
      this.resp = err;
    }
  }
}
