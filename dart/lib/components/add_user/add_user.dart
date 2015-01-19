library add_user;

import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWay, NgTwoWay;
import 'dart:async' as async;

@Component(
  selector: 'add-user',
  templateUrl: 'packages/pritunl/components/add_user/add_user.html'
)
class AddUserComp extends modal_content.ModalContent {
  user.User model;

  @NgTwoWay('orgs')
  organizations.Organizations orgs;

  AddUserComp(this.model);

  void submit(async.Future closeHandler()) {
    var valid = this.validateForms({
      'name': '.name',
      'organization': '.org',
      'email': '.email',
    });

    if (valid != true) {
      return;
    }

    this.model.create(['name', 'organization', 'email']).then((_) {
      super.submit(closeHandler);
    });
  }
}
