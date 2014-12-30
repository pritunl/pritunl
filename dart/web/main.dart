library pritunl;

import 'package:pritunl/routers/routers.dart' as routers;
import 'package:pritunl/components/status/status.dart' as status;
import 'package:pritunl/components/rating/rating.dart' as rating;

import 'package:angular/angular.dart' as ng;
import 'package:angular/application_factory.dart' as appfactory;

class Pritunl extends ng.Module {
  Pritunl() {
    this.bind(rating.RatingComponent);
    this.bind(status.StatusComponent);
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
      .addModule(new Pritunl())
      .run();
}
