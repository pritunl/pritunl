library modal;

import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' as ng;

class ModalBase implements ng.ShadowRootAware {
  var root;

  var _alertElem;
  get alertElem {
    if (this._alertElem == null) {
      this._alertElem = this.root.querySelector('alert');
    }
    return this._alertElem;
  }

  var _alert;
  get alert {
    if (this._alert == null) {
      this._alert = utils.getDirective(this.alertElem);
    }
    return this._alert;
  }

  onShadowRoot(root) {
    this.root = root;
  }

  setAlert(text) {
    if (text != null && this.alert.text == text) {
      this.alert.flash();
    }
    else {
      this.alert.text = text;
    }
  }

  reset() {
    var form = this.root.querySelector('form-control');
    form.classes.remove('danger');
    this.alert.text = null;
  }

  cancel() {
    this.reset();
  }
}
