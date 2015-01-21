library users_comp;

import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Component, NgTwoWay;
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

  var _usersLen = 0;
  var _users;
  @NgTwoWay('users')
  set users(usrs.Users val) {
    if (val.length != this._usersLen) {
      var userItems = this.root.querySelectorAll('.user-item');
      var diff = (val.length - this._usersLen).abs();
      var insAnim = (val.length - diff).abs();
      var remAnim = (this._usersLen - diff).abs();
      var i = 0;

      for (var user in val) {
        if (i >= insAnim) {
          user.animated = 'animated-ins';
        }
        else {
          user.animated = null;
        }
        i += 1;
      }

      for (i = 0; i < userItems.length; i++) {
        if (i >= remAnim) {
          userItems[i].classes.add('animated-rem');
        }
        else {
          userItems[i].classes.remove('animated-rem');
        }
      }
    }

    this._usersLen = val.length;
    this._users = val;
  }
  get users {
    return this._users;
  }

  UsersComp(this.http);

  void attach() {
    if (this.users.page == null) {
      this.users.page = 0;
    }
    this.update();
  }

  void update() {
    this.users.fetch();
  }
}
