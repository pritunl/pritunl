library modal;

import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' as ng;

class ModalBase implements ng.ShadowRootAware {
  var root;
  var model;
  var _errorForm;

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
    if (text != null && this.alert.text != null) {
      this.alert.flash();
    }
    this.alert.text = text;
  }

  clearAlert() {
    this.setAlert(null);
  }

  setFormError(selector, error) {
    if (error is Error) {
      error = error.toString();
    }

    var form = this.root.querySelector(selector);

    if (this._errorForm != null && this._errorForm != form) {
      this._errorForm.classes.remove('danger');
    }
    this._errorForm = form;

    form.classes.add('danger');
    this.setAlert(error);
  }

  clearFormError() {
    if (this._errorForm != null) {
      this._errorForm.classes.remove('danger');
      this._errorForm = null;
    }
    this.clearAlert();
  }

  reset() {
    this.clearFormError();

    if (this.alert != null) {
      this.alert.text = null;
    }

    if (this.model != null) {
      this.model.reset();
    }
  }

  cancel() {
    this.reset();
  }
}
