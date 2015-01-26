library user_key_links_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'user-key-links',
  templateUrl: 'packages/pritunl/components/user_key_links/user_key_links.html'
)
class UserKeyLinksComp extends modal_content.ModalContent {
  @NgOneWayOneTime('model')
  user.User model;

  void show() {
  }
}
