library modal;

import 'package:angular/angular.dart' show Component, NgAttr, NgCallback;

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

  var _okText;
  @NgAttr('ok-text')
  get okText {
    if (this._okText != null && this._okText != '') {
      return this._okText;
    }
    return 'Ok';
  }
  set okText(val) {
    this._okText = val;
  }

  var _cancelText;
  @NgAttr('cancel-text')
  get cancelText {
    if (this._cancelText != null && this._cancelText != '') {
      return this._cancelText;
    }
    return 'Cancel';
  }
  set cancelText(val) {
    this._cancelText = val;
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
