library form_control;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'form-control',
  template: '<input type="{{type}}" placeholder="{{placeholder}}"/>',
  cssUrl: 'packages/pritunl/components/form_control/form_control.css'
)
class FormControlComp {
  @NgAttr('type')
  var type;

  @NgAttr('placeholder')
  var placeholder;
}
