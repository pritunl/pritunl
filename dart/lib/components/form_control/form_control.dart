library form_control;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr, NgModel;

@Component(
  selector: 'form-control',
  template: '<input ng-type="type" placeholder="{{placeholder}}" '
    'ng-model="model"/>',
  cssUrl: 'packages/pritunl/components/form_control/form_control.css'
)
class FormControlComp {
  @NgAttr('type')
  var type;

  @NgAttr('placeholder')
  var placeholder;

  @NgTwoWay('model')
  var model;
}
