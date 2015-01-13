library add_org;

import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'add-org',
  templateUrl: 'packages/pritunl/components/add_org/add_org.html',
  cssUrl: 'packages/pritunl/components/add_org/add_org.css'
)
class AddOrgComp implements ng.ShadowRootAware {
  var org;
  var root;

  AddOrgComp(organization.Organization this.org);

  onShadowRoot(root) {
    this.root = root;
  }

  add() {
    if (this.org.name == null) {
      var form = this.root.querySelector('form-control');
      form.classes.add('danger');
      return false;
    }

    this.org.create(['name']).then(() {
      this.org.clear();
    });
  }

  cancel() {
    this.org.clear();
  }
}
