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

  var alertType;
  var alertText;

  add() {
    if (this.org.name == null) {
      var form = this.root.querySelector('form-control');
      form.classes.add('danger');
      this.alertType = 'danger';
      this.alertText = 'Organization name cannot be empty';
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
