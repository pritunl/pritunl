library user_del;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'dart:async' as async;

@Component(
  selector: 'user-del',
  templateUrl: 'packages/pritunl/components/user_del/user_del.html'
)
class UserDelComp extends modal_content.ModalContent {
  @NgOneWay('users')
  Set<user.User> users;

  void submit(async.Future closeHandler()) {
    super.submit(closeHandler);
  }
}
