library status_comp;

import 'package:pritunl/models/status.dart' as stus;

import 'package:angular/angular.dart' show Component;

@Component(
    selector: 'x-status',
    templateUrl: 'packages/pritunl/components/status/status.html',
    cssUrl: 'packages/pritunl/components/status/status.css'
)
class StatusComp {
  stus.Status model;

  StatusComp(this.model) {
    this.update();
  }

  void update() {
    this.model.fetch();
  }
}
