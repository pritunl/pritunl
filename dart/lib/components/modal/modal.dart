library modal;

import 'package:angular/angular.dart' show Component, NgCallback;

@Component(
  selector: 'modal',
  templateUrl: 'packages/pritunl/components/modal/modal.html',
  cssUrl: 'packages/pritunl/components/modal/modal.css'
)
class ModalComp {
  var state;

  @NgCallback('on-ok')
  var onOk;

  @NgCallback('on-cancel')
  var onCancel;

  ModalComp() {
  }

  open() {
    this.state = true;
  }

  close(submit) {
    var returnVal;
    if (submit) {
      returnVal = this.onOk();
    }
    else {
      returnVal = this.onCancel();
    }

    if (returnVal == false) {
      return;
    }

    this.state = false;
  }

  softClose(target) {
    if (target.classes.contains('modal')) {
      this.close(false);
    }
  }

  hardClose() {
    this.close(false);
  }

  submit() {
    this.close(true);
  }
}
