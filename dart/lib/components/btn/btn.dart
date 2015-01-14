library btn;

import 'package:angular/angular.dart' show Component, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'btn',
  template: '<button type="{{btnType}}" ng-class="[type, size]" '
    'ng-disabled="disabled"><content></content></button>',
  cssUrl: 'packages/pritunl/components/btn/btn.css'
)
class BtnComp implements ng.ShadowRootAware {
  @NgAttr('type')
  var type;

  @NgAttr('size')
  var size;

  @NgAttr('width')
  var width;

  @NgAttr('min-width')
  var minWidth;

  @NgAttr('height')
  var height;

  @NgAttr('min-height')
  var minHeight;

  var btnType;
  @NgAttr('form-submit')
  get formSubmit {
    return this.btnType == 'submit';
  }
  set formSubmit(value) {
    if (value == '') {
      this.btnType = 'submit';
    }
    else {
      this.btnType = 'button';
    }
  }

  var _disabled;
  @NgAttr('disabled')
  get disabled {
    return this._disabled;
  }
  set disabled(val) {
    if (val == '') {
      this._disabled = true;
    }
    else {
      this._disabled = false;
    }
  }

  onShadowRoot(root) {
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
