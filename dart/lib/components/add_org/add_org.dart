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

  AddOrgComp(organization.Organization this.org);

  add() {
    this.org.save();
  }

  cancel() {
    this.org.clear();
  }
}
