library noselect;

import 'dart:html' as dom;
import 'package:angular/angular.dart' show Decorator;

@Decorator(
  selector: '[no-select]'
)
class NoSelectDec {
  var element;

  NoSelectDec(dom.Element this.element) {
    element.onMouseDown.listen((evt) {
      evt.preventDefault();
    });
  }
}
