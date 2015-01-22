library organization_comp;

import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component, NgOneWay;

@Component(
  selector: 'organization',
  templateUrl: 'packages/pritunl/components/organization/organization.html',
  cssUrl: 'packages/pritunl/components/organization/organization.css'
)
class OrganizationComp {
  bool showHidden;

  @NgOneWay('model')
  organization.Organization model;

  toggleHidden() {
    this.showHidden = this.showHidden != true;
  }
}
