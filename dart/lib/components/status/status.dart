library status;

import 'package:pritunl/models/status.dart' as status;

import 'package:angular/angular.dart' show Component;

@Component(
    selector: 'status',
    templateUrl: 'packages/pritunl/components/status/status.html',
    cssUrl: 'packages/pritunl/components/status/status.css'
)
class StatusComp {
  status.Status model;

  StatusComp(this.model) {
    this.update();
  }

  void update() {
    this.model.fetch();
  }
}
