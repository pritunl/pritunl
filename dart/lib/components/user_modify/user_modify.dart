library user_modify_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/user.dart' as usr;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'x-user-modify',
  templateUrl: 'packages/pritunl/components/user_modify/user_modify.html'
)
class UserModifyComp extends modal_content_base.ModalContent {
  usr.User model;

  @NgOneWayOneTime('model')
  usr.User origModel;

  void show() {
    this.model = this.origModel.clone();
  }

  async.Future submit(async.Future closeHandler()) {
    var valid = this.validateForms({
      'name': '.name',
      'email': '.email',
    });

    if (valid != true) {
      return null;
    }
    this.okDisabled = true;

    return this.model.save(['name', 'email']).then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully modified user.', 'success');
    }).catchError((err) {
      logger.severe('Failed to modified user', err);
      this.setHttpError(
        'Failed to modified user, server error occurred.', err);
    }).whenComplete(() {
      this.okDisabled = false;
    });
  }
}
