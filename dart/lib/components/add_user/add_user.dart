library add_user;

import 'package:pritunl/collections/organizations.dart' as organizations;

import 'package:pritunl/components/modal_base/modal_base.dart' as modal_base;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWay, NgTwoWay;

@Component(
  selector: 'add-user',
  templateUrl: 'packages/pritunl/components/add_user/add_user.html'
)
class AddUserComp extends modal_base.ModalBase {
  user.User model;
  String org;

  @NgTwoWay('orgs')
  organizations.Organizations orgs;

  AddUserComp(this.model);

  bool submit() {
    return false;
  }
}
