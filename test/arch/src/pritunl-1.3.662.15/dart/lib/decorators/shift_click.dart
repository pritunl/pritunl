library shift_click_dec;

import 'package:angular/angular.dart' show Decorator, NgCallback;
import 'dart:html' as dom;

@Decorator(
  selector: '[shift-click]'
)
class ShiftClickDec {
  @NgCallback('shift-click')
  Function callback;

  ShiftClickDec(dom.Element element) {
    element.onClick.listen((evt) {
      if (evt.shiftKey) {
        this.callback();
      }
    });
  }
}
