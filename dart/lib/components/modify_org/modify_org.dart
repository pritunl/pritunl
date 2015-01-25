library modify_org_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'modify-org',
  templateUrl: 'packages/pritunl/components/modify_org/modify_org.html'
)
class ModifyOrgComp extends modal_content.ModalContent {
  organization.Organization model;

  @NgOneWayOneTime('model')
  organization.Organization origModel;

  void show() {
    this.model = this.origModel.clone();
  }

  void submit(async.Future closeHandler()) {
    var valid = this.validateForms({
      'name': '.name',
    });

    if (valid != true) {
      return;
    }

    this.model.save(['name']).then((_) {
      super.submit(closeHandler);
    });
  }
}
