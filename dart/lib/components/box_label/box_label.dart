library box_label;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'box-label',
  template: '<span class="{{labelType}}"><content></content></span>',
  cssUrl: 'packages/pritunl/components/box_label/box_label.css'
)
class BoxLabelComp {
  @NgAttr('label-type')
  var labelType;
}
