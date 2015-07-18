library utils;

import 'package:angular/introspection.dart' as introspection;
import 'dart:html' as dom;
import 'dart:math' as math;
import 'dart:js' as js;

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

String uuid() {
  var rand = new math.Random();
  var id = '';

  for (var i = 0; i < 8; i++) {
    id += ((1 + rand.nextDouble()) * 0x10000).floor().toRadixString(
      16).substring(1);
  }

  return id;
}

String getDomain() {
  return '${dom.window.location.protocol}//${dom.window.location.host}';
}

void printColor(dynamic obj, String color) {
  js.context['console'].callMethod('log', [
    '%c$obj', 'color: $color']);
}
