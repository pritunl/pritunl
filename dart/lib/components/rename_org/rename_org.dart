library rename_org_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'rename-org',
  templateUrl: 'packages/pritunl/components/rename_org/rename_org.html'
)
class RenameOrgComp extends modal_content.ModalContent {
  String newName;
  organization.Organization model;

  @NgOneWayOneTime('model')
  organization.Organization origModel;

  void submit(async.Future closeHandler()) {
    this.model = this.origModel.clone();
    this.model.name = this.newName;

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
