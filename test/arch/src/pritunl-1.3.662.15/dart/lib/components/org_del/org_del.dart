library org_del_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'x-org-del',
  templateUrl: 'packages/pritunl/components/org_del/org_del.html'
)
class OrgDelComp extends modal_content_base.ModalContent {
  bool okDisabled = true;
  bool locked;

  @NgOneWayOneTime('model')
  organization.Organization model;

  var _nameConfirm;
  void set nameConfirm(String val) {
    if (val == this.model.name && this.locked != true) {
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
    this.locked = true;
    this.okDisabled = true;

    return this.model.destroy().then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully deleted organization.', 'success');
    }).catchError((err) {
      logger.severe('Failed to delete organization', err);
      this.setHttpError(
        'Failed to delete organization, server error occurred.', err);
    }).whenComplete(() {
      this.locked = false;
      this.okDisabled = false;
    });
  }
}
