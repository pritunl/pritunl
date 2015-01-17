library modal;

import 'package:angular/angular.dart' show Component, NgAttr, NgCallback;
import 'dart:html' as dom;

@Component(
  selector: 'modal',
  templateUrl: 'packages/pritunl/components/modal/modal.html',
  cssUrl: 'packages/pritunl/components/modal/modal.css'
)
class ModalComp {
  bool state;

  @NgCallback('on-ok')
  Function onOk;

  @NgCallback('on-cancel')
  Function onCancel;

  var _okText;
  @NgAttr('ok-text')
  String get okText {
    if (this._okText != null && this._okText != '') {
      return this._okText;
    }
    return 'Ok';
  }
  set okText(String val) {
    this._okText = val;
  }

  var _cancelText;
  @NgAttr('cancel-text')
  String get cancelText {
    if (this._cancelText != null && this._cancelText != '') {
      return this._cancelText;
    }
    return 'Cancel';
  }
  set cancelText(String val) {
    this._cancelText = val;
  }

  void open() {
    this.state = true;
  }

  void close([bool submit]) {
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

  void softClose(dom.Element target) {
    if (target.classes.contains('modal')) {
      this.close(false);
    }
  }

  void hardClose() {
    this.close(false);
  }

  void submit() {
    this.close(true);
  }
}
