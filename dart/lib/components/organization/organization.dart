library organization_comp;

import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Component, NgOneWay,
  NgOneWayOneTime;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Component(
  selector: 'organization',
  templateUrl: 'packages/pritunl/components/organization/organization.html',
  cssUrl: 'packages/pritunl/components/organization/organization.css'
)
class OrganizationComp implements ng.ScopeAware, ng.ShadowRootAware {
  ng.Http http;
  dom.ShadowRoot root;
  bool showHidden;

  @NgOneWayOneTime('model')
  organization.Organization org;

  @NgOneWayOneTime('selected')
  Set<usr.User> selected;

  OrganizationComp(this.http);

  String _curMessage;
  String get message {
    if (this.org.users.loadingLong == true) {
      this._curMessage = 'Loading...';
    }
    else if (this.org.users.noUsers == true) {
      if (this.org.users.loading == true) {
        return _curMessage;
      }
      else if (this.org.users.search == null) {
        this._curMessage = 'There are no users in this organization';
      }
      else {
        this._curMessage = 'No users found';
      }
    }
    else {
      this._curMessage = null;
    }
    return this._curMessage;
  }

  void toggleHidden() {
    this.showHidden = this.showHidden != true;
  }

  void select(usr.User user, bool shift) {
    if (this.selected.contains(user)) {
      this.selected.remove(user);
    } else {
      this.selected.add(user);
    }
  }

  void set scope(ng.Scope scope) {
    scope.on('users_updated').listen((evt) {
      if (evt.data.resourceId == this.org.id) {
        this.org.users.fetch();
      }
    });
  }

  void onShadowRoot(dom.ShadowRoot root) {
    this.root = root;
  }

  void update() {
    this.org.users.fetch();
  }
}
