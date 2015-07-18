library server_del_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/server.dart' as svr;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'x-server-del',
  templateUrl: 'packages/pritunl/components/server_del/server_del.html'
)
class ServerDelComp extends modal_content_base.ModalContent {
  bool okDisabled = true;
  bool locked;

  @NgOneWayOneTime('model')
  svr.Server model;

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
      new alrt.Alert('Successfully deleted server.', 'success');
    }).catchError((err) {
      logger.severe('Failed to delete server', err);
      this.setHttpError(
        'Failed to delete server, server error occurred.', err);
    }).whenComplete(() {
      this.locked = false;
      this.okDisabled = false;
    });
  }
}
