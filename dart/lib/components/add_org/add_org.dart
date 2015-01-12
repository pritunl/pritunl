library add_org;

import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'add-org',
  templateUrl: 'packages/pritunl/components/add_org/add_org.html',
  cssUrl: 'packages/pritunl/components/add_org/add_org.css'
)
class AddOrgComp {
  var org;
  var orgName;

  AddOrgComp(organization.Organization this.org);

  addOrg() {
    this.org.name = this.orgName;
    print('${this.org.name}');
  }
}
