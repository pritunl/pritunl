library organizations;

import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'organizations',
  templateUrl: 'packages/pritunl/components/organizations/organizations.html',
  cssUrl: 'packages/pritunl/components/organizations/organizations.css'
)
class OrganizationsComp {
  organizations.Organizations orgs;

  OrganizationsComp(this.orgs) {
    this.update();
  }

  void onAddOrg(organization.Organization model) {
    print('add: $model');
  }

  void update() {
    this.orgs.fetch();
  }
}
