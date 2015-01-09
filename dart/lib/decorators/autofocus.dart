library autofocus;

import 'dart:html' as dom;
import 'package:angular/angular.dart' show Decorator;
import 'package:angular/angular.dart' as ng;

@Decorator(
  selector: '[autofocus]'
)
class AutoFocusDec implements ng.AttachAware {
  var element;

  AutoFocusDec(dom.Element element);

  attach() {
    element.focus();
  }
}
