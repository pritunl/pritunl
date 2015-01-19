library add_org_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'add-org',
  templateUrl: 'packages/pritunl/components/add_org/add_org.html'
)
class AddOrgComp extends modal_content.ModalContent {
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
