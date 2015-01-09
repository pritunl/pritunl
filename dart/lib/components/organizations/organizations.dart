library organizations;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

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
