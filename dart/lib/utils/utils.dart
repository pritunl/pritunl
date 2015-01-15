library utils;

import 'package:angular/introspection.dart' as introspection;
import 'dart:html' as dom;

getDirective(node) {
  while (node != null) {
    var probe = introspection.elementExpando[node];

    if (probe != null) {
      var directives = probe.directives;
      if (directives.length > 0) {
        return directives[0];
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
