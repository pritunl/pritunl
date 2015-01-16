library add_org;

import 'package:pritunl/bases/modal.dart' as modal_base;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'add-org',
  templateUrl: 'packages/pritunl/components/add_org/add_org.html'
)
class AddOrgComp extends modal_base.ModalBase {
  var model;

  AddOrgComp(organization.Organization this.model);

  submit() {
    var valid = this.validateForms({
      'name': '.name',
    });

    if (valid != true) {
      return false;
    }

    this.model.create(['name']).then((_) {
      super.submit();
    });
  }
}
