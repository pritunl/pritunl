library organizations_comp;

import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/collections/users.dart' as users;
import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'organizations',
  templateUrl: 'packages/pritunl/components/organizations/organizations.html',
  cssUrl: 'packages/pritunl/components/organizations/organizations.css'
)
class OrganizationsComp {
  Set<user.User> selected = new Set();
  organizations.Organizations orgs;

  OrganizationsComp(this.orgs) {
    this.update();
  }

  void onAddOrg(organization.Organization model) {
    print('addOrg: $model');
  }

  void onAddUser(user.User model) {
    print('addUser: $model');
  }

  void onAddUserBulk(users.Users collection) {
    print('addUserBulk: $collection');
  }

  void update() {
    this.orgs.fetch();
  }
}
