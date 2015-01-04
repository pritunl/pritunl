library box_label;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'box-label',
  templateUrl: 'packages/pritunl/components/box_label/box_label.html',
  cssUrl: 'packages/pritunl/components/box_label/box_label.css'
)
class BoxLabelComp {
  @NgAttr('label-type')
  var labelType;
}
