library organizations_comp;

import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/collections/users.dart' as usrs;
import 'package:pritunl/models/user.dart' as usr;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'x-organizations',
  templateUrl: 'packages/pritunl/components/organizations/organizations.html',
  cssUrl: 'packages/pritunl/components/organizations/organizations.css'
)
class OrganizationsComp implements ng.AttachAware, ng.ScopeAware {
  Set<usr.User> selected = new Set();
  organizations.Organizations orgs;
  ng.Http http;

  OrganizationsComp(this.http) {
    this.orgs = new organizations.Organizations(this.http);
    this.update();
  }

  void update() {
    this.orgs.fetch().catchError((err) {
      logger.severe('Failed to load organizations', err);
      new alrt.Alert('Failed to load organizations, server error occurred.',
        'danger');
    });
  }

  void set scope(ng.Scope scope) {
    scope.on('organizations_updated').listen((evt) {
      this.update();
    });
  }

  void attach() {
    this.orgs.onAdd = (model) {
      model.users = new usrs.Users(this.http);
      model.users.org = model.id;
      model.users.onRemove = (userModel) {
        this.selected.remove(userModel);
      };
      if (model.users.page == null) {
        model.users.page = 0;
      }
      model.users.fetch();
    };
  }

  String _curMessage;
  String get message {
    if (this.orgs.loadingLong == true) {
      this._curMessage = 'Loading...';
    }
    else if (this.orgs.length == 0) {
      if (this.orgs.loading != true) {
        this._curMessage = 'There are no organizations on this host';
      }
    }
    else {
      this._curMessage = null;
    }
    return _curMessage;
  }
}
