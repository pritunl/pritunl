library modal_content_base;

import 'package:pritunl/exceptions.dart';
import 'package:pritunl/components/alert/alert.dart' as alrt;
import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' show NgCallback;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:async' as async;

abstract class ModalContent implements ng.ShadowRootAware {
  dom.ShadowRoot root;
  dynamic model;
  dom.Element _errorForm;
  String alertType;
  String alertText;
  bool okDisabled;
  bool cancelDisabled;

  @NgCallback('on-submit')
  Function onSubmit;

  alrt.AlertComp get alert {
    var alertElem = this.root.querySelector('alert');
    return utils.getDirective(alertElem, alrt.AlertComp);
  }

  void onShadowRoot(dom.ShadowRoot root) {
    this.root = root;
  }

  void show() {
  }

  void setAlert(String text, [String type]) {
    if (type != null) {
      this.alertType = type;
    }

    if (text != null && this.alertText != null) {
      this.alert.flash();
    }

    this.alertText = text;
  }

  void clearAlert() {
    this.setAlert(null);
  }

  void setHttpError(String defaultMsg, HttpError err) {
    if (err.errorMsg != null) {
      this.setAlert(err.errorMsg, 'danger');
    }
    else {
      this.setAlert(defaultMsg, 'danger');
    }
  }

  void setFormError(String selector, dynamic error, [String type]) {
    if (error is Error) {
      error = error.toString();
    }

    if (type == null) {
      type = 'danger';
    }

    var form = this.root.querySelector(selector);

    if (this._errorForm != null && (
      this._errorForm != form ||
      this.alertType != type
    )) {
      this._errorForm.classes.remove(this.alertType);
    }
    this._errorForm = form;

    form.classes.add(type);
    this.setAlert(error, type);
  }

  void clearFormError() {
    if (this._errorForm != null) {
      this._errorForm.classes.remove(this.alertType);
      this._errorForm = null;
    }
    this.clearAlert();
  }

  bool validateForms(Map<String, String> forms) {
    for (var name in forms.keys) {
      try {
        this.model.validate(name);
      } catch(err) {
        this.setFormError(forms[name], err);
        return false;
      }
    }
    this.clearFormError();
    return true;
  }

  void reset() {
    this.clearFormError();
    this.clearAlert();

    if (this.model != null) {
      this.model.clear();
    }
  }

  async.Future submit(async.Future closeHandler()) {
    return closeHandler().then((_) {
      if (onSubmit != null) {
        var clone;
        if (this.model != null) {
          clone = this.model.clone();
        }

        this.reset();
        this.onSubmit({r'$model': clone});
      }
      else {
        this.reset();
      }
    });
  }

  void cancel(async.Future closeHandler()) {
    closeHandler().then((_) {
      this.reset();
    });
  }
}
