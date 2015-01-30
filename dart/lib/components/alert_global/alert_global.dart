library alert_global_comp;

import 'package:pritunl/alert.dart' as alrt;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'dart:collection' as collection;

@Component(
  selector: 'alert-global',
  template: '<alert ng-repeat="alert in alerts" type="alert.type" '
    'text="alert.text" on-dismiss="onDismiss(alert)" dismissible></alert>',
  cssUrl: 'packages/pritunl/components/alert_global/alert_global.css'
)
class AlertGlobalComp {
  collection.Queue<alrt.Alert> alerts = alrt.alerts;

  void onDismiss(alrt.Alert alert) {
    this.alerts.remove(alert);
  }
}
