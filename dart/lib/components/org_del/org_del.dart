library org_del_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'org-del',
  templateUrl: 'packages/pritunl/components/org_del/org_del.html'
)
class OrgDelComp extends modal_content.ModalContent {
  bool okDisabled = true;

  @NgOneWayOneTime('model')
  organization.Organization model;

  var _nameConfirm;
  void set nameConfirm(String val) {
    if (val == this.model.name) {
      this.okDisabled = false;
    }
    else {
      this.okDisabled = true;
    }
    this._nameConfirm = val;
  }
  String get nameConfirm {
    return this._nameConfirm;
  }

  void reset() {
    this.clearFormError();
    this.clearAlert();

    this.nameConfirm = null;
  }

  async.Future submit(async.Future closeHandler()) {
    return this.model.destroy().then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully deleted organization.', 'success');
    }).catchError((err) {
      logger.severe('Failed to delete organization', err);
      this.setAlert('Failed to delete organization, server error occurred.',
      'danger');
    });
  }
}
