library utils;

import 'package:angular/introspection.dart' as introspection;
import 'dart:html' as dom;

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
