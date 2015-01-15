library alert;

import 'package:angular/angular.dart' show Component, NgAttr, NgTwoWay,
  NgCallback;
import 'package:angular/angular.dart' as ng;
import 'dart:async' as async;

@Component(
  selector: 'alert',
  template: '<div class="alert" ng-class="type" ng-if="text != null" '
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

  flash() {
    var alertElem = this.root.querySelector('.alert');

    alertElem.classes.add('flash-on');
    alertElem.classes.remove('flash-off');
    new async.Future.delayed(new Duration(milliseconds: 180), () {
      alertElem.classes.add('flash-off');
      alertElem.classes.remove('flash-on');
    }).then((_) {
      return new async.Future.delayed(new Duration(milliseconds: 180), () {
        alertElem.classes.add('flash-on');
        alertElem.classes.remove('flash-off');
      });
    }).then((_) {
      return new async.Future.delayed(new Duration(milliseconds: 180), () {
        alertElem.classes.add('flash-off');
        alertElem.classes.remove('flash-on');
      });
    });
  }

  close() {
    this.text = null;
  }
}
