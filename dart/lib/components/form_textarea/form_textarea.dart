library form_textarea_comp;

import 'package:pritunl/bases/form_control/form_control.dart' as
  form_control_base;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'x-form-textarea',
  template: '<textarea placeholder="{{placeholder}}" '
    'ng-model="model" tooltip="{{formTooltip}}" rows="{{rows}}" '
    'spellcheck="{{spellcheck}}"></textarea>',
  cssUrl: 'packages/pritunl/components/form_textarea/form_textarea.css'
)
class FormTextareaComp extends form_control_base.FormControlBase {
  String controlSelector = 'input';

  @NgAttr('form-tooltip')
  String formTooltip;

  @NgAttr('rows')
  String rows;

  @NgAttr('spellcheck')
  String spellcheck;

  @NgAttr('placeholder')
  String placeholder;

  @NgTwoWay('model')
  String model;
}
