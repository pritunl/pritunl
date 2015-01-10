library organization;

import 'package:angular/angular.dart' show Component, NgTwoWay;

@Component(
  selector: 'organization',
  templateUrl: 'packages/pritunl/components/organization/organization.html',
  cssUrl: 'packages/pritunl/components/organization/organization.css'
)
class OrganizationComp {
  @NgTwoWay('model')
  var model;

  toggleHidden() {
    model.users.hidden = model.users.hidden != true;
  }
}
