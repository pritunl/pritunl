library add_org;

import 'package:pritunl/bases/modal.dart' as modal_base;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'add-org',
  templateUrl: 'packages/pritunl/components/add_org/add_org.html',
  cssUrl: 'packages/pritunl/components/add_org/add_org.css'
)
class AddOrgComp extends modal_base.ModalBase {
  var org;

  AddOrgComp(organization.Organization this.org);

  reset() {
    super.reset();
    this.org.clear();
  }

  add() {
    if (this.org.name == null) {
      var form = this.root.querySelector('form-control');
      form.classes.add('danger');

      this.setAlert('Organization name cannot be empty');

      return false;
    }

    this.org.create(['name']).then((_) {
      this.reset();
    });
  }
}
