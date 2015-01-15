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
  var alertText;

  AddOrgComp(organization.Organization this.org);

  onShadowRoot(root) {
    this.root = root;
  }

  reset() {
    var form = this.root.querySelector('form-control');
    form.classes.remove('danger');
    this.alertText = null;
    this.org.clear();
  }

  add() {
    if (this.org.name == null) {
      var form = this.root.querySelector('form-control');
      form.classes.add('danger');
      this.alertText = 'Organization name cannot be empty';
      return false;
    }

    this.org.create(['name']).then((_) {
      this.reset();
    });
  }

  cancel() {
    this.reset();
  }
}
