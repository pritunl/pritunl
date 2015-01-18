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
  dom.Element element;

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
