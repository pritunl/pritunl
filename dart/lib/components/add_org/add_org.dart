library add_org;

import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'add-org',
  templateUrl: 'packages/pritunl/components/add_org/add_org.html',
  cssUrl: 'packages/pritunl/components/add_org/add_org.css'
)
class AddOrgComp implements ng.ShadowRootAware {
  var org;
  var root;

  AddOrgComp(organization.Organization this.org);

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

  reset() {
    var form = this.root.querySelector('form-control');
    form.classes.remove('danger');
    this.org.clear();
    this.alert.text = null;
  }

  add() {
    if (this.org.name == null) {
      var form = this.root.querySelector('form-control');
      form.classes.add('danger');

      if (this.alert.text != null) {
        this.alert.flash();
      }
      else {
        this.alert.text = 'Organization name cannot be empty';
      }

      return false;
    }

    this.org.create(['name']).then((_) {
      this.reset();
    });
  }

  cancel() {
    this.reset();
  }
}
