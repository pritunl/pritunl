library form_input_comp;

import 'package:pritunl/bases/form_control/form_control.dart' as
  form_control_base;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'form-input',
  template: '<input ng-type="type" placeholder="{{placeholder}}" '
    'ng-model="model" tooltip="{{formTooltip}}"/>',
  cssUrl: 'packages/pritunl/components/form_input/form_input.css'
)
class FormInputComp extends form_control_base.FormControlBase {
  String controlSelector = 'input';

  @NgAttr('form-tooltip')
  String formTooltip;

  @NgAttr('type')
  String type;

  @NgAttr('placeholder')
  String placeholder;

  @NgTwoWay('model')
  String model;
}
