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
  var model;

  AddOrgComp(organization.Organization this.model);

  submit() {
    try {
      this.model.validate('name');
    } catch(err) {
      this.setFormError('.name', err);
      return false;
    }

    this.model.create(['name']).then((_) {
      this.reset();
    });
  }
}
