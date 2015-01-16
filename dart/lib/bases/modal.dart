library modal;

import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' show NgCallback;
import 'package:angular/angular.dart' as ng;

class ModalBase implements ng.ShadowRootAware {
  var root;
  var model;
  var _errorForm;

  @NgCallback('on-submit')
  var onSubmit;

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

  setAlert(text, [type]) {
    if (type != null) {
      this.alert.type = type;
    }

    if (text != null && this.alert.text != null) {
      this.alert.flash();
    }

    this.alert.text = text;
  }

  clearAlert() {
    this.setAlert(null);
  }

  setFormError(selector, error, [type]) {
    if (error is Error) {
      error = error.toString();
    }

    if (type == null) {
      type = 'danger';
    }

    var form = this.root.querySelector(selector);

    if (this._errorForm != null && (
          this._errorForm != form ||
          this.alert.type != type
        )) {
      this._errorForm.classes.remove(this.alert.type);
    }
    this._errorForm = form;

    form.classes.add(type);
    this.setAlert(error, type);
  }

  clearFormError() {
    if (this._errorForm != null) {
      this._errorForm.classes.remove(this.alert.type);
      this._errorForm = null;
    }
    this.clearAlert();
  }

  validateForms(forms) {
    for (final name in forms.keys) {
      try {
        this.model.validate(name);
      } catch(err) {
        this.setFormError(forms[name], err);
        return false;
      }
    }
    return true;
  }

  submit() {
    var clone = this.model.clone();
    this.reset();
    this.onSubmit({r'$model': clone});
  }

  reset() {
    this.clearFormError();

    if (this.alert != null) {
      this.alert.text = null;
    }

    if (this.model != null) {
      this.model.clear();
    }
  }

  cancel() {
    this.reset();
  }
}
