library alert_comp;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay,
  NgTwoWay, NgCallback;
import 'package:angular/angular.dart' as ng;
import 'dart:async' as async;
import 'dart:html' as dom;

@Component(
  selector: 'alert',
  template: '<div class="alert" ng-class="type" ng-if="text != null" '
    'ng-animate>{{text}}<content></content><btn type="close-color" '
    'ng-click="close()" ng-if="dismissible"></btn></div>',
  cssUrl: 'packages/pritunl/components/alert/alert.css'
)
class AlertComp implements ng.ShadowRootAware {
  dom.ShadowRoot root;

  @NgOneWay('type')
  String type;

  @NgTwoWay('text')
  String text = '';

  var _dismissible;
  @NgAttr('dismissible')
  set dismissible(dynamic val) {
    if (val == '') {
      this._dismissible = true;
    }
    else {
      this._dismissible = false;
    }
  }
  bool get dismissible {
    return this._dismissible;
  }

  var _alertElem;
  dom.Element get alertElem {
    if (this._alertElem == null) {
      this._alertElem = this.root.querySelector('.alert');
    }
    return this._alertElem;
  }

  void onShadowRoot(dom.ShadowRoot root) {
    this.root = root;
  }

  void flash() {
    var delay = const Duration(milliseconds: 180);

    this.alertElem.classes.add('flash-on');
    this.alertElem.classes.remove('flash-off');
    new async.Future.delayed(delay, () {
      this.alertElem.classes.add('flash-off');
      this.alertElem.classes.remove('flash-on');
    }).then((_) {
      return new async.Future.delayed(delay, () {
        this.alertElem.classes.add('flash-on');
        this.alertElem.classes.remove('flash-off');
      });
    }).then((_) {
      return new async.Future.delayed(delay, () {
        this.alertElem.classes.add('flash-off');
        this.alertElem.classes.remove('flash-on');
      });
    }).then((_) {
      return new async.Future.delayed(delay, () {
        this.alertElem.classes.remove('flash-off');
      });
    });
  }

  void close() {
    this.text = null;
  }
}
