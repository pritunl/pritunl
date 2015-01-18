library user_comp;

import 'package:pritunl/collections/users.dart' as users;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgAttr, NgTwoWay;

@Component(
  selector: 'user',
  templateUrl: 'packages/pritunl/components/user/user.html',
  cssUrl: 'packages/pritunl/components/user/user.css'
)
class UserComp {
  bool showServers;

  @NgTwoWay('model')
  user.User model;

  @NgTwoWay('collection')
  users.Users collection;

  @NgAttr('selected')
  bool selected;
}
