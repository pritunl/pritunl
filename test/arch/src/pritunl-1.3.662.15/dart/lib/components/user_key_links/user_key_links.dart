library user_key_links_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/user.dart' as usr;
import 'package:pritunl/models/key.dart' as ky;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;

@Component(
  selector: 'x-user-key-links',
  templateUrl: 'packages/pritunl/components/user_key_links/user_key_links.html',
  cssUrl: 'packages/pritunl/components/user_key_links/user_key_links.css'
)
class UserKeyLinksComp extends modal_content_base.ModalContent {
  ky.Key model;

  @NgOneWayOneTime('model')
  usr.User user;

  UserKeyLinksComp(this.model);

  void show() {
    this.model.user = this.user.id;
    this.model.org = this.user.organization;
    this.model.fetch();
  }
}
