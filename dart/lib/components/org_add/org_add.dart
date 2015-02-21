library org_add_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component;
import 'dart:async' as async;

@Component(
  selector: 'x-org-add',
  templateUrl: 'packages/pritunl/components/org_add/org_add.html'
)
class OrgAddComp extends modal_content_base.ModalContent {
  organization.Organization model;

  OrgAddComp(this.model);

  async.Future submit(async.Future closeHandler()) {
    var valid = this.validateForms({
      'name': '.name',
    });

    if (valid != true) {
      return null;
    }
    this.okDisabled = true;

    return this.model.create(['name']).then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully added organization.', 'success');
    }).catchError((err) {
      logger.severe('Failed to add organization', err);
      this.setHttpError('Failed to add organization, server error occurred.',
        err);
    }).whenComplete(() {
      this.okDisabled = false;
    });
  }
}
