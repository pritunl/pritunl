library alert;

import 'package:angular/angular.dart' show Component, NgAttr, NgTwoWay,
  NgCallback;

@Component(
  selector: 'alert',
  template: '<div class="alert" ng-class="type" ng-if="text != null"'
    '>{{text}}<btn type="close-color" ng-click="close()" '
    'ng-if="dismissible"></btn></div>',
  cssUrl: 'packages/pritunl/components/alert/alert.css'
)
class AlertComp {
  var _dismissible;
  @NgAttr('dismissible')
  get dismissible {
    return this._dismissible;
  }
  set dismissible(val) {
    if (val == '') {
      this._dismissible = true;
    }
    else {
      this._dismissible = false;
    }
  }

  @NgAttr('type')
  var type;

  @NgTwoWay('text')
  var text;

  close() {
    this.text = null;
  }
}
