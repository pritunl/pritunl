library organization_comp;

import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/collections/users.dart' as usrs;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Component, NgOneWay;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Component(
  selector: 'organization',
  templateUrl: 'packages/pritunl/components/organization/organization.html',
  cssUrl: 'packages/pritunl/components/organization/organization.css'
)
class OrganizationComp implements ng.AttachAware, ng.ShadowRootAware {
  ng.Http http;
  dom.ShadowRoot root;
  Map<String, String> animated = {};
  Map<String, bool> showServers = {};
  Map<String, bool> selected = {};
  bool showHidden;

  @NgOneWay('model')
  organization.Organization org;

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
  void onUsersImport(List<usr.User> users) {
    if (users != null && users.length != this._usersLen) {
      var userItems;
      var diff = (users.length - this._usersLen).abs();
      var insAnim = (users.length - diff).abs();
      var remAnim = (this._usersLen - diff).abs();
      var aniamted = {};

      if (this.root != null) {
        userItems = this.root.querySelectorAll('.user-item');
      }
      else {
        userItems = [];
      }

      for (var i = 0; i < users.length; i++) {
        if (i >= insAnim) {
          aniamted[users[i]] = 'animated-ins';
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

      this._usersLen = users.length;
    }
  }

  void toggleHidden() {
    this.showHidden = this.showHidden != true;
  }

  void attach() {
    this.org.users.onImport = this.onUsersImport;
    if (this.org.users.page == null) {
      this.org.users.page = 0;
    }
    this.update();
  }

  void onShadowRoot(dom.ShadowRoot root) {
    this.root = root;
  }

  void update() {
    this.org.users.fetch();
  }

  void onDelOrg(organization.Organization model) {
    print('delOrg: $model');
  }
}
