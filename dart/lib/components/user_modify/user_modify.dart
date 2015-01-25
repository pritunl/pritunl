library user_modify_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'dart:async' as async;

@Component(
  selector: 'user-modify',
  templateUrl: 'packages/pritunl/components/user_modify/user_modify.html'
)
class UserModifyComp extends modal_content.ModalContent {
  user.User model;

  @NgOneWayOneTime('model')
  user.User origModel;

  void show() {
    this.model = this.origModel.clone();
  }

  void submit(async.Future closeHandler()) {
    var valid = this.validateForms({
      'name': '.name',
      'email': '.email',
    });

    if (valid != true) {
      return;
    }

    this.model.save(['name', 'email']).then((_) {
      super.submit(closeHandler);
    });
  }
}
