library user_email_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/user.dart' as usr;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'dart:async' as async;

@Component(
  selector: 'x-user-email',
  templateUrl: 'packages/pritunl/components/user_email/user_email.html',
  cssUrl: 'packages/pritunl/components/user_email/user_email.css'
)
class UserEmailComp extends modal_content_base.ModalContent {
  String okText = 'Send';
  String noCancel;
  Map<usr.User, String> userClass = {};
  Map<usr.User, String> userMsg = {};

  @NgOneWay('users')
  Set<usr.User> users;

  String getUserData(usr.User user) {
    var data = user.name;

    if (user.email != null) {
      data += ' (${user.email})';
    }

    if (this.userMsg[user] != null) {
      data += ' - ${this.userMsg[user]}';
    }

    return data;
  }

  async.Future submit(async.Future closeHandler()) {
    if (this.okText == 'Close') {
      return super.submit(closeHandler).then((_) {
        this.noCancel = null;
        this.okText = 'Send';
        this.userClass.clear();
        this.userMsg.clear();
      });
    }
    this.okDisabled = true;

    return async.Future.wait(this.users.map((user) {
      if (user.email == null) {
        return new async.Future.sync(() {
          this.userClass[user] = 'warning-text';
          this.userMsg[user] = 'Skipped';
        });
      }

      return user.mailKey().then((_) {
        this.userClass[user] = 'success-text';
        this.userMsg[user] = 'Sent';
      }).catchError((err) {
        this.userClass[user] = 'danger-text';
        this.userMsg[user] = 'Error';
        return new async.Future.error(err);
      });
    })).then((_) {
      this.noCancel = 'no-cancel';
      this.okText = 'Close';
      this.setAlert('Successfully emailed users.', 'success');
    }).catchError((err) {
      logger.severe('Failed to email users', err);
      this.setHttpError('Failed to email users, server error occurred.', err);
    }).whenComplete(() {
      this.okDisabled = false;
    });
  }
}
