library user_add;

import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as user;
import 'package:pritunl/alert.dart' as alrt;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'dart:async' as async;

@Component(
  selector: 'user-add',
  templateUrl: 'packages/pritunl/components/user_add/user_add.html'
)
class UserAddComp extends modal_content.ModalContent {
  user.User model;

  @NgOneWay('orgs')
  organizations.Organizations orgs;

  UserAddComp(this.model);

  async.Future submit(async.Future closeHandler()) {
    var valid = this.validateForms({
      'name': '.name',
      'organization': '.org',
      'email': '.email',
    });

    if (valid != true) {
      return null;
    }

    return this.model.create(['name', 'organization', 'email']).then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully added user.', 'success');
    }).catchError((err) {
      logger.severe('Failed to add user', err);
      this.setAlert('Failed to add user, server error occurred.', 'danger');
    });
  }
}
