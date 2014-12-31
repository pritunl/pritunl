library noselect;

import 'dart:html' as dom;
import 'package:angular/angular.dart' show Decorator;

@Decorator(
  selector: '[no-select]'
)
class NoSelectDec {
  NoSelectDec(dom.Element element) {
    element.onMouseDown.listen((evt) {
      evt.preventDefault();
    });
  }
}
