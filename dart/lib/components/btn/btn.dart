library btn;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'btn',
  template: '<button type="button" ng-class="btnType" ng-disabled="disabled">'
    '<content></content></button>',
  cssUrl: 'packages/pritunl/components/btn/btn.css'
)
class BtnComp {
  @NgAttr('btn-type')
  var btnType;

  var _disabled;
  @NgAttr('disabled')
  get disabled {
    return this._disabled;
  }
  set disabled(value) {
    if (value == '') {
      this._disabled = true;
    }
    else {
      this._disabled = false;
    }
  }
}
