library organization_comp;

import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component, NgTwoWay;

@Component(
  selector: 'organization',
  templateUrl: 'packages/pritunl/components/organization/organization.html',
  cssUrl: 'packages/pritunl/components/organization/organization.css'
)
class OrganizationComp {
  @NgTwoWay('model')
  organization.Organization model;

  toggleHidden() {
    this.model.users.hidden = this.model.users.hidden != true;
  }
}
