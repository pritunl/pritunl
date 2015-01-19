library form_select_comp;

import 'package:pritunl/bases/form_control/form_control.dart' as
  form_control_base;

import 'package:angular/angular.dart' show Component, NgCallback, NgTwoWay,
  NgOneWay, NgAttr;
import 'package:angular/angular.dart' as ng;
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

  void onShadowRoot(dom.ShadowRoot root) {
    this.element = root.querySelector('select');

    if (this.width == null) {
      this.width = '200px';
    }
    else {
      this.width = this.width;
    }

    this.height = this.height;
    this.padding = this.padding;
  }
}
