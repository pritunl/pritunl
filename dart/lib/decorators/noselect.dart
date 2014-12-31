library noselect;

import 'dart:html' as dom;
import 'package:angular/angular.dart' show Decorator;

@Decorator(
  selector: '[tooltip]'
)
class NoSelectDec {
  var element;

  NoSelectDec(dom.Element this.element);
}
