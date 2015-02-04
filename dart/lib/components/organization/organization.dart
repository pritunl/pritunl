library organization_comp;

import 'package:pritunl/collections/users.dart' as usrs;
import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Component, NgOneWay,
  NgOneWayOneTime;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:async' as async;

@Component(
  selector: 'organization',
  templateUrl: 'packages/pritunl/components/organization/organization.html',
  cssUrl: 'packages/pritunl/components/organization/organization.css'
)
class OrganizationComp implements ng.ScopeAware, ng.ShadowRootAware {
  ng.Http http;
  dom.ShadowRoot root;
  Map<usr.User, String> animated = {};
  bool showHidden;

  @NgOneWayOneTime('model')
  organization.Organization org;

  @NgOneWayOneTime('selected')
  Set<usr.User> selected;

  OrganizationComp(this.http);

  String get message {
    if (this.org.users.loadingLong == true) {
      return 'Loading...';
    }
    else if (this.org.users.noUsers == true) {
      if (this.org.users.search == null) {
        return 'There are no users in this organization';
      }
      return 'No users found';
    }
    return null;
  }

  var _usersLen = 0;
  void onUsersImport() {
    if (this.org.users != null && this.org.users.length != this._usersLen) {
      var userItems;
      var diff = (this.org.users.length - this._usersLen).abs();
      var insAnim = (this.org.users.length - diff).abs();
      var remAnim = (this._usersLen - diff).abs();
      var aniamted = {};

      if (this.root != null) {
        userItems = this.root.querySelectorAll('.user-item');
      }
      else {
        userItems = [];
      }

      for (var i = 0; i < this.org.users.length; i++) {
        if (i >= insAnim) {
          aniamted[this.org.users[i]] = 'animated-ins';
        }
      }

      this.animated = aniamted;

      for (var i = 0; i < userItems.length; i++) {
        if (i >= remAnim) {
          userItems[i].classes.add('animated-rem');
        }
        else {
          userItems[i].classes.remove('animated-rem');
        }
      }

      this._usersLen = this.org.users.length;
    }
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

  void attach() {
    this.org.users.onChange = this.clearUser;
    this.org.users.onRemove = this.clearUser;
    this.org.users.onImport = this.onUsersImport;
    this.org.users.eventRegister((_) => this.update());

    if (this.org.users.page == null) {
      this.org.users.page = 0;
    }
    this.update();
  }

  void set scope(ng.Scope scope) {
    scope.on('users_updated').listen((evt) {
      if (evt.data.resourceId == this.org.id) {
        print('users_updated');
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
