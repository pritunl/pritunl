library organizations_comp;

import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'organizations',
  templateUrl: 'packages/pritunl/components/organizations/organizations.html',
  cssUrl: 'packages/pritunl/components/organizations/organizations.css'
)
class OrganizationsComp implements ng.AttachAware, ng.DetachAware {
  Set<user.User> selected = new Set();
  organizations.Organizations orgs;

  OrganizationsComp(this.orgs) {
    this.update();
  }

  void update() {
    this.orgs.fetch();
  }

  void attach() {
    this.orgs.eventRegister((_) => this.update());
  }

  void detach() {
    this.orgs.eventDeregister();
  }
}
