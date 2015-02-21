library user_del_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/user.dart' as usr;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'dart:async' as async;

@Component(
  selector: 'x-user-del',
  templateUrl: 'packages/pritunl/components/user_del/user_del.html',
  cssUrl: 'packages/pritunl/components/user_del/user_del.css'
)
class UserDelComp extends modal_content_base.ModalContent {
  @NgOneWay('users')
  Set<usr.User> users;

  async.Future submit(async.Future closeHandler()) {
    return async.Future.wait(this.users.map((user) {
      return user.destroy();
    })).then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully deleted users.', 'success');
    }).catchError((err) {
      logger.severe('Failed to delete users', err);
      this.setHttpError('Failed to delete users, server error occurred.', err);
    }).whenComplete(() {
      this.okDisabled = false;
    });
  }
}
