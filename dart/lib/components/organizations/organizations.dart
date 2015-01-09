library organizations;

import 'package:pritunl/collections/organizations.dart' as organizations;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'organizations',
  templateUrl: 'packages/pritunl/components/organizations/organizations.html',
  cssUrl: 'packages/pritunl/components/organizations/organizations.css'
)
class OrganizationsComp {
  var orgs;

  OrganizationsComp(organizations.Organizations this.orgs) {
    this.update();
  }

  update() {
    this.orgs.fetch();
  }
}
