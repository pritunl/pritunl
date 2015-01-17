library add_org;

import 'package:pritunl/components/modal_base/modal_base.dart' as modal_base;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'add-org',
  templateUrl: 'packages/pritunl/components/add_org/add_org.html',
  cssUrl: modal_base.BASE_CSS_URL
)
class AddOrgComp extends modal_base.ModalBase {
  organization.Organization model;

  AddOrgComp(this.model);

  bool submit() {
    var valid = this.validateForms({
      'name': '.name',
    });

    if (valid != true) {
      return false;
    }

    this.model.create(['name']).then((_) {
      super.submit();
    });

    return true;
  }
}
