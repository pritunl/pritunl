library form_input;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Component(
  selector: 'form-input',
  template: '<input ng-type="type" placeholder="{{placeholder}}" '
    'ng-model="model" tooltip="{{formTooltip}}"/>',
  cssUrl: 'packages/pritunl/components/form_input/form_input.css'
)
class FormInputComp implements ng.ShadowRootAware {
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

  void onShadowRoot(dom.ShadowRoot root) {
    var elem = root.querySelector('input');

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
