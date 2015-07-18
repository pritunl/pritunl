library alert_global_comp;

import 'package:pritunl/alert.dart' as alrt;

import 'package:angular/angular.dart' show Component;
import 'dart:collection' as collection;

@Component(
  selector: 'x-alert-global',
  template: '<x-alert ng-repeat="alert in alerts" type="alert.type" '
    'text="alert.text" on-dismiss="onDismiss(alert)" dismissible></x-alert>'
)
class AlertGlobalComp {
  collection.Queue<alrt.Alert> alerts = alrt.alerts;

  void onDismiss(alrt.Alert alert) {
    this.alerts.remove(alert);
  }
}
