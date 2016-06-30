library noselect_dec;

import 'package:angular/angular.dart' show Decorator;
import 'dart:html' as dom;

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
