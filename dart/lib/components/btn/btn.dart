library btn_comp;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Component(
  selector: 'x-btn',
  template: '<button type="{{btnType}}" ng-class="[type, size]" '
    'ng-disabled="disabled"><content></content></button>',
  cssUrl: 'packages/pritunl/components/btn/btn.css'
)
class BtnComp implements ng.ShadowRootAware {
  String btnType;

  @NgAttr('type')
  String type;

  @NgAttr('size')
  String size;

  @NgAttr('width')
  String width;

  @NgAttr('min-width')
  String minWidth;

  @NgAttr('height')
  String height;

  @NgAttr('min-height')
  String minHeight;

  @NgOneWay('disabled')
  bool disabled;

  @NgAttr('form-submit')
  bool get formSubmit {
    return this.btnType == 'submit';
  }
  void set formSubmit(dynamic val) {
    if (val == '' || val == 'form-submit') {
      this.btnType = 'submit';
    }
    else {
      this.btnType = 'button';
    }
  }

  void onShadowRoot(dom.ShadowRoot root) {
    var elem = root.querySelector('button');

    if (this.width != null) {
      elem.style.width = this.width;
    }
    if (this.minWidth != null) {
      elem.style.minWidth = this.minWidth;
    }
    if (this.height != null) {
      elem.style.height = this.height;
    }
    if (this.minHeight != null) {
      elem.style.minHeight = this.minHeight;
    }
  }
}
