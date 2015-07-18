library modal_comp;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay;
import 'dart:html' as dom;

@Component(
  selector: 'x-modal',
  templateUrl: 'packages/pritunl/components/modal/modal.html',
  cssUrl: 'packages/pritunl/components/modal/modal.css'
)
class ModalComp {
  bool state;
  Function submit;
  Function cancel;

  @NgAttr('title')
  String title;

  @NgOneWay('ok-disabled')
  bool okDisabled;

  @NgOneWay('cancel-disabled')
  bool cancelDisabled;

  var _advanced;
  @NgAttr('advanced')
  get advanced {
    return this._advanced;
  }
  void set advanced(val) {
    if (val == '') {
      this._advanced = true;
    }
    else {
      this._advanced = false;
    }
  }

  var _okText;
  @NgAttr('ok-text')
  String get okText {
    if (this._okText != null && this._okText != '') {
      return this._okText;
    }
    return 'Ok';
  }
  void set okText(String val) {
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
  void set cancelText(String val) {
    this._cancelText = val;
  }

  var _noCancel;
  @NgAttr('no-cancel')
  void set noCancel(dynamic val) {
    if (val == '' || val == 'no-cancel') {
      this._noCancel = true;
    }
    else {
      this._noCancel = false;
    }
  }
  bool get noCancel {
    return this._noCancel;
  }

  var _noOk;
  @NgAttr('no-ok')
  void set noOk(dynamic val) {
    if (val == '' || val == 'no-ok') {
      this._noOk = true;
    }
    else {
      this._noOk = false;
    }
  }
  bool get noOk {
    return this._noOk;
  }

  void softClose(dom.Element target) {
    if (target.classes.contains('modal')) {
      this.cancel();
    }
  }

  void hardClose() {
    this.cancel();
  }
}
