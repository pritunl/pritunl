library routers;

import 'package:pritunl/routers/main.dart' as main;

import 'package:angular/angular.dart' as ng;

class RoutersMod extends ng.Module {
  RoutersMod() {
    this.bind(
      ng.RouteInitializerFn,
      toValue: main.MainRout
    );
    this.bind(
      ng.NgRoutingUsePushState,
      toValue: new ng.NgRoutingUsePushState.value(false)
    );
  }
}
