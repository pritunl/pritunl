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
class OrganizationComp implements ng.AttachAware, ng.ShadowRootAware {
  ng.Http http;
  dom.ShadowRoot root;
  Map<usr.User, String> animated = {};
  Map<usr.User, bool> showServers = {};
  Set<String> _userIdsSet;
  Map<String, usr.User> _userIdsMap;
  bool showHidden;

  @NgOneWayOneTime('model')
  organization.Organization org;

  @NgOneWay('selected')
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
  void onUsersImport(List<usr.User> users) {
    var userIdsSet = new Set();
    var userIdsMap = {};

    users.forEach((user) {
      userIdsSet.add(user.id);
      userIdsMap[user.id] = user;
    });

    if (this._userIdsSet != null) {
      this._userIdsSet.difference(userIdsSet).forEach((id) {
        this.selected.remove(this._userIdsMap[id]);
      });
    }
    this._userIdsSet = userIdsSet;
    this._userIdsMap = userIdsMap;

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

  void select(usr.User user, bool shift) {
    if (this.selected.contains(user)) {
      this.selected.remove(user);
    } else {
      this.selected.add(user);
    }
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
