library status;

import 'package:pritunl/models/status.dart' as status;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

@Component(
    selector: 'status',
    templateUrl: 'packages/pritunl/components/status/status.html',
    cssUrl: 'packages/pritunl/components/status/status.css'
)
class StatusComp {
  var http;
  var model;

  StatusComp(ng.Http this.http, status.Status this.model) {
    this.update();
  }

  update() {
    this.model.fetch();
  }
}
