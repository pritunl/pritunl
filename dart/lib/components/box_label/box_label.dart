library box_label;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'box-label',
  template: '<span ng-class="type"><content></content></span>',
  cssUrl: 'packages/pritunl/components/box_label/box_label.css'
)
class BoxLabelComp {
  @NgAttr('type')
  var type;
}
