library shift_click;

import 'package:angular/angular.dart' show Decorator, NgCallback;
import 'dart:html' as dom;

@Decorator(
  selector: '[shift-click]'
)
class ShiftClickDec {
  @NgCallback('shift-click')
  var callback;

  ShiftClickDec(dom.Element element) {
    element.onClick.listen((evt) {
      if (evt.shiftKey) {
        this.callback();
      }
    });
  }
}
