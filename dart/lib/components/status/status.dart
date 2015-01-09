library status;

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

  StatusComp(ng.Http this.http) {
    this.update();
  }

  update() {
    this.http.get('/status').then((response) {
      this.model = response.data;
    });
  }
}
