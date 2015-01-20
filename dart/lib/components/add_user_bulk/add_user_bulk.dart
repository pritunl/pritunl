library add_user_bulk_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user_bulk.dart' as user_bulk;

import 'package:angular/angular.dart' show Component;
import 'dart:async' as async;

@Component(
  selector: 'add-user-bulk',
  templateUrl: 'packages/pritunl/components/add_user_bulk/add_user_bulk.html'
)
class AddUserBulkComp extends modal_content.ModalContent {
  String users;

  user_bulk.UserBulk model;

  AddUserBulkComp(this.model);

  void submit(async.Future closeHandler()) {
    print(this.users);

    return;
    this.model.create(['name']).then((_) {
      super.submit(closeHandler);
    });
  }
}
