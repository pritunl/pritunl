library form_select_comp;

import 'package:pritunl/bases/form_control/form_control.dart' as
  form_control_base;

import 'package:angular/angular.dart' show Component, NgCallback, NgTwoWay,
  NgOneWay, NgAttr;
import 'dart:html' as dom;

@Component(
  selector: 'form-select',
  template: '<select ng-model="model" tooltip="{{formTooltip}}">'
    '<option ng-repeat="colModel in collection" '
    'ng-value="optValue({\'\$model\': colModel})">'
    '{{optText({\'\$model\': colModel})}}</option></select>',
  cssUrl: 'packages/pritunl/components/form_select/form_select.css'
)
class FormSelectComp extends form_control_base.FormControlBase {
  String controlSelector = 'select';

  @NgAttr('form-tooltip')
  String formTooltip;

  @NgAttr('type')
  String type;

  @NgAttr('placeholder')
  String placeholder;

  @NgTwoWay('model')
  String model;

  @NgOneWay('collection')
  Iterable collection;

  @NgCallback('opt-value')
  Function optValue;

  @NgCallback('opt-text')
  Function optText;

  onShadowRoot(dom.ShadowRoot root) {
    if (this.model == null && this.collection != null) {
      for (var model in this.collection) {
        this.model = this.optValue({r'$model': model});
        break;
      }
    }

    super.onShadowRoot(root);
  }
}
