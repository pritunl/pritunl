library tooltip;

import 'package:angular/angular.dart' show Component, NgTwoWay;
import 'dart:html' as dom;

@Component(
  selector: 'tooltip',
  templateUrl: 'packages/pritunl/components/tooltip/tooltip.html',
  cssUrl: 'packages/pritunl/components/tooltip/tooltip.css'
)
class TooltipComp {
  var element;

  @NgTwoWay('state')
  var state;

  TooltipComp(dom.Element this.element);

  show(x, y) {
    this.element.style
      ..position = 'absolute'
      ..left = '${x}px'
      ..top = '${y}px';
    this.state = true;
  }

  hide() {
    this.state = false;
  }
}
