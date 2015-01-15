library alert;

import 'package:angular/angular.dart' show Component, NgAttr, NgTwoWay,
  NgCallback;

@Component(
  selector: 'alert',
  template: '<div class="alert {{type}}" ng-class="" ng-if="text != null" '
    'ng-animate>{{text}}<btn type="close-color" ng-click="close()" '
    'ng-if="dismissible"></btn></div>',
  cssUrl: 'packages/pritunl/components/alert/alert.css'
)
class AlertComp implements ng.ShadowRootAware {
  var root;

  @NgAttr('type')
  var type;

  @NgTwoWay('text')
  var text;

  var _dismissible;
  @NgAttr('dismissible')
  set dismissible(val) {
    if (val == '') {
      this._dismissible = true;
    }
    else {
      this._dismissible = false;
    }
  }
  get dismissible {
    return this._dismissible;
  }

  onShadowRoot(root) {
    this.root = root;
  }

  close() {
    this.text = null;
  }
}
