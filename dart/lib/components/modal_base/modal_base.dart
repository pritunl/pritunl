library modal;

import 'package:pritunl/components/alert/alert.dart' as alrt;
import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' show NgCallback;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

const String BASE_CSS_URL = 'packages/pritunl/components/'
  'modal_base/modal_base.css';

class ModalBase implements ng.ShadowRootAware {
  dom.ShadowRoot root;
  mdl.Model model;
  dom.Element _errorForm;
  bool state;

  @NgCallback('on-submit')
  Function onSubmit;

  var _alertElem;
  dom.Element get alertElem {
    if (this._alertElem == null) {
      this._alertElem = this.root.querySelector('alert');
    }
    return this._alertElem;
  }

  var _alert;
  alrt.AlertComp get alert {
    if (this._alert == null) {
      this._alert = utils.getDirective(this.alertElem);
    }
    return this._alert;
  }

  void onShadowRoot(dom.ShadowRoot root) {
    this.root = root;
  }

  void show() {
    this.state = true;
  }

  void hide() {
    this.state = false;
  }

  void setAlert(String text, [String type]) {
    if (type != null) {
      this.alert.type = type;
    }

    if (text != null && this.alert.text != null) {
      this.alert.flash();
    }

    this.alert.text = text;
  }

  void clearAlert() {
    this.setAlert(null);
  }

  void setFormError(String selector, Error error, [String type]) {
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
    this.setAlert(error.toString(), type);
  }

  void clearFormError() {
    if (this._errorForm != null) {
      this._errorForm.classes.remove(this.alert.type);
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
    return true;
  }

  void submit() {
    var clone = this.model.clone();
    this.reset();
    this.onSubmit({r'$model': clone});
  }

  void reset() {
    this.clearFormError();

    if (this.alert != null) {
      this.alert.text = null;
    }

    if (this.model != null) {
      this.model.clear();
    }
  }

  void cancel() {
    this.reset();
  }
}
