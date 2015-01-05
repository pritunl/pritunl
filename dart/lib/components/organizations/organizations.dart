library boilerplate;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'organizations',
  templateUrl: 'packages/pritunl/components/organizations/organizations.html',
  cssUrl: 'packages/pritunl/components/organizations/organizations.css'
)
class OrganizationsComp {
  var http;
  var orgs;

  OrganizationsComp(ng.Http this.http) {
    this.update();
  }

  update() {
    this.http.get('/orgs').then((response) {
      this.orgs = response.data;
    });
  }
}
