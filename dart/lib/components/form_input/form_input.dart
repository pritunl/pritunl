library form_input_comp;

import 'package:pritunl/bases/form_control/form_control.dart' as
  form_control_base;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay,
  NgTwoWay;

@Component(
  selector: 'x-form-input',
  template: '<input ng-type="type" placeholder="{{placeholder}}" '
    'ng-readonly="readonly" ng-model="model" value="{{value}}" '
    'tooltip="{{formTooltip}}"/>',
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

  @NgOneWay('value')
  String value;

  var _readonly;
  @NgAttr('readonly')
  void set readonly(dynamic val) {
    if (val == '' || val == 'readonly') {
      this._readonly = true;
    }
    else {
      this._readonly = false;
    }
  }
  bool get readonly {
    return this._readonly;
  }
}
