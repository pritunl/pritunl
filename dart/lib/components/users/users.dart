library users_comp;

import 'package:pritunl/collections/users.dart' as usrs;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Component, NgOneWay, NgTwoWay;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Component(
  selector: 'users',
  templateUrl: 'packages/pritunl/components/users/users.html',
  cssUrl: 'packages/pritunl/components/users/users.css'
)
class UsersComp implements ng.AttachAware, ng.ShadowRootAware {
  ng.Http http;
  dom.ShadowRoot root;
  Map<usrs.Users, String> _animated = {};
  Map<String, bool> showServers = {};
  Map<String, bool> selected = {};

  UsersComp(this.http);

  @NgOneWay('show-hidden')
  bool showHidden;

  var _usersLen = 0;
  var _users;
  @NgOneWay('users')
  set users(usrs.Users val) {
    this._users = val;
  }
  get users {
    if (this._users != null && this._users.length != this._usersLen) {
      var userItems = this.root.querySelectorAll('.user-item');
      var diff = (this._users.length - this._usersLen).abs();
      var insAnim = (this._users.length - diff).abs();
      var remAnim = (this._usersLen - diff).abs();
      var aniamted = {};

      for (var i = 0; i < this._users.length; i++) {
        if (i >= insAnim) {
          aniamted[this._users[i]] = true;
        }
      }

      this._animated = aniamted;

      for (var i = 0; i < userItems.length; i++) {
        if (i >= remAnim) {
          userItems[i].classes.add('animated-rem');
        }
        else {
          userItems[i].classes.remove('animated-rem');
        }
      }

      this._usersLen = this._users.length;
    }

    return this._users;
  }

  String aniamted(usr.User user) {
    if (this._animated[user] == true) {
      return 'animated-ins';
    }
    return null;
  }

  void attach() {
    if (this.users.page == null) {
      this.users.page = 0;
    }
    this.update();
  }

  void onShadowRoot(dom.ShadowRoot root) {
    this.root = root;
  }

  void update() {
    this.users.fetch();
  }
}
