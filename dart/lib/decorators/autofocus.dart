library autofocus_dec;

import 'package:angular/angular.dart' show Decorator;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Decorator(
  selector: '[autofocus]'
)
class AutoFocusDec implements ng.AttachAware {
  dom.Element element;

  AutoFocusDec(this.element);

  void attach() {
    element.focus();
  }
}
