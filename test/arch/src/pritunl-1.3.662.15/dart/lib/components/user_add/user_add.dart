library user_add_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/models/user.dart' as usr;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'dart:async' as async;

@Component(
  selector: 'x-user-add',
  templateUrl: 'packages/pritunl/components/user_add/user_add.html'
)
class UserAddComp extends modal_content_base.ModalContent {
  usr.User model;

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
    this.okDisabled = true;

    return this.model.create(['name', 'organization', 'email']).then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully added user.', 'success');
    }).catchError((err) {
      logger.severe('Failed to add user', err);
      this.setHttpError('Failed to add user, server error occurred.', err);
    }).whenComplete(() {
      this.okDisabled = false;
    });
  }
}
