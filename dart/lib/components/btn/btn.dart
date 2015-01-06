library btn;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'btn',
  template: '<button type="button" ng-class="[type, size]" '
    'ng-disabled="disabled"><content></content></button>',
  cssUrl: 'packages/pritunl/components/btn/btn.css'
)
class BtnComp {
  @NgAttr('type')
  var type;

  @NgAttr('size')
  var size;

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
