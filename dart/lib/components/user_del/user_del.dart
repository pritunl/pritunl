library user_del;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'dart:async' as async;

@Component(
  selector: 'user-del',
  templateUrl: 'packages/pritunl/components/user_del/user_del.html',
  cssUrl: 'packages/pritunl/components/user_del/user_del.css'
)
class UserDelComp extends modal_content.ModalContent {
  @NgOneWay('users')
  Set<usr.User> users;

  async.Future _destroyUsers(Iterator<usr.User> users) {
    users.moveNext();
    if (users.current == null) {
      return null;
    }

    return users.current.destroy().then((_) {
      return this._destroyUsers(users);
    });
  }

  void submit(async.Future closeHandler()) {
    this._destroyUsers(this.users.iterator).then((_) {
      super.submit(closeHandler);
    });
  }
}
