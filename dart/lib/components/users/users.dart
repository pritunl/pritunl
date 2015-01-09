library users;

import 'package:angular/angular.dart' show Component, NgTwoWay;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'users',
  templateUrl: 'packages/pritunl/components/users/users.html',
  cssUrl: 'packages/pritunl/components/users/users.css'
)
class UsersComp implements ng.AttachAware {
  var http;

  @NgTwoWay('users')
  var users;

  UsersComp(ng.Http this.http);

  attach() {
    this.update();
  }

  update() {
    this.users.fetch();
  }
}
