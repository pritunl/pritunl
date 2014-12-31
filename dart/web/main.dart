library pritunl;

import 'package:pritunl/routers/routers.dart' as routers;
import 'package:pritunl/components/components.dart' as components;

import 'package:angular/angular.dart' as ng;
import 'package:angular/application_factory.dart' as appfactory;

class Pritunl extends ng.Module {
  Pritunl() {
    this.bind(
      ng.RouteInitializerFn,
      toValue: routers.Main
    );
    this.bind(
      ng.NgRoutingUsePushState,
      toValue: new ng.NgRoutingUsePushState.value(false)
    );
  }
}

void main() {
  appfactory.applicationFactory()
      .addModule(new components.ComponentsMod())
      .addModule(new Pritunl())
      .run();
}
