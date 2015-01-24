library del_org_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/organization.dart' as organization;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'del-org',
  templateUrl: 'packages/pritunl/components/del_org/del_org.html'
)
class DelOrgComp extends modal_content.ModalContent {
  bool okDisabled = true;

  @NgOneWayOneTime('model')
  organization.Organization model;

  var _nameConfirm;
  set nameConfirm(String val) {
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
  }

  void onDelOrg(organization.Organization model) {
    print('delOrg: $model');
  }

  void submit(async.Future closeHandler()) {
    this.model.create().then((_) {
    });
  }
}
