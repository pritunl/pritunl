library form_control;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'form-control',
  template: '<input ng-type="type" placeholder="{{placeholder}}" ng-model="model" tooltip="{{formTooltip}}"/>',
  cssUrl: 'packages/pritunl/components/form_control/form_control.css'
)
class FormControlComp implements ng.ShadowRootAware {
  @NgAttr('form-tooltip')
  var formTooltip;

  @NgAttr('padding')
  var padding;

  @NgAttr('width')
  var width;

  @NgAttr('height')
  var height;

  @NgAttr('type')
  var type;

  @NgAttr('placeholder')
  var placeholder;

  @NgTwoWay('model')
  var model;

  onShadowRoot(root) {
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
