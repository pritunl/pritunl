library users_comp;

import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Component, NgTwoWay;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'users',
  templateUrl: 'packages/pritunl/components/users/users.html',
  cssUrl: 'packages/pritunl/components/users/users.css'
)
class UsersComp implements ng.AttachAware {
  ng.Http http;

  @NgTwoWay('users')
  usrs.Users users;

  UsersComp(this.http);

  void attach() {
    this.update();
  }

  void update() {
    this.users.fetch();
  }
}
