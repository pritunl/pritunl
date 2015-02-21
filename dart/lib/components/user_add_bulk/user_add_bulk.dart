library user_add_bulk_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/collections/users.dart' as usrs;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'dart:async' as async;

@Component(
  selector: 'x-user-add-bulk',
  templateUrl: 'packages/pritunl/components/user_add_bulk/user_add_bulk.html'
)
class UserAddBulkComp extends modal_content_base.ModalContent {
  String users;
  usrs.Users model;

  @NgOneWay('orgs')
  organizations.Organizations orgs;

  UserAddBulkComp(this.model);

  async.Future submit(async.Future closeHandler()) {
    var usersLines;

    if (this.users != null) {
      usersLines = this.users.split('\n');
    }

    if (usersLines == null || usersLines.length == 0) {
      this.setFormError('.users', 'User list cannot be empty');
      return null;
    }

    for(var line in usersLines) {
      var data = {};
      line = line.split(',');

      if (line[0] == '') {
        continue;
      }

      data['name'] = line[0];

      if (line.length > 1 && line[1] != '') {
        data['email'] = line[1];
      }

      this.model.add(data);
    }

    var valid = this.validateForms({
      'name': '.users',
      'email': '.users',
    });

    if (valid != true) {
      this.model.clear();
      return null;
    }
    this.okDisabled = true;

    return this.model.create(['name', 'email']).then((_) {
      return super.submit(closeHandler);
    }).then((_) {
      new alrt.Alert('Successfully added users.', 'success');
    }).catchError((err) {
      logger.severe('Failed to add users', err);
      this.setHttpError('Failed to add users, server error occurred.', err);
    }).whenComplete(() {
      this.okDisabled = false;
    });
  }

  void reset() {
    this.users = '';
    super.reset();
  }
}
