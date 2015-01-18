library form_select_comp;

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
class FormSelectComp implements ng.ShadowRootAware {
  @NgAttr('form-tooltip')
  String formTooltip;

  @NgAttr('padding')
  String padding;

  @NgAttr('width')
  String width;

  @NgAttr('height')
  String height;

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
    var elem = root.querySelector('select');

    if (this.padding != null) {
      elem.style.padding = this.padding;
    }
    if (this.width != null) {
      elem.style.width = this.width;
    }
    if (this.height != null) {
      elem.style.height = this.height;
    }
  }
}
