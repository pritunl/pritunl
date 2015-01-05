library status;

import 'package:pritunl/settings/settings.dart' as settings;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
    selector: 'status',
    templateUrl: 'packages/pritunl/components/status/status.html',
    cssUrl: 'packages/pritunl/components/status/status.css'
)
class StatusComp {
  var http;
  var model;

  StatusComp(ng.Http this.http) {
    this.update();
  }

  update() {
    this.http.get('/status').then((response) {
      this.model = response.data;
    });
  }
}
