library tooltip;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'tooltip',
  templateUrl: 'packages/pritunl/components/tooltip/tooltip.html',
  cssUrl: 'packages/pritunl/components/tooltip/tooltip.css'
)
class TooltipComp {
  @NgTwoWay('state')
  var state;

  show() {
    this.state = true;
  }

  hide() {
    this.state = false;
  }
}
