library form_input_comp;

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
  dom.Element element;

  @NgAttr('form-tooltip')
  String formTooltip;

  var _width;
  @NgAttr('width')
  String get width {
    return this._width;
  }
  set width(String width) {
    if (this.element != null) {
      this.element.style.width = width;
    }
    this._width = width;
  }

  var _height;
  @NgAttr('height')
  String get height {
    return this._height;
  }
  set height(String height) {
    if (this.element != null) {
      this.element.style.height = height;
    }
    this._height = height;
  }

  var _padding;
  @NgAttr('padding')
  String get padding {
    return this._padding;
  }
  set padding(String padding) {
    if (this.element != null) {
      this.element.style.padding = padding;
    }
    this._padding = padding;
  }

  @NgAttr('type')
  String type;

  @NgAttr('placeholder')
  String placeholder;

  @NgTwoWay('model')
  String model;

  void onShadowRoot(dom.ShadowRoot root) {
    this.element = root.querySelector('input');

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
