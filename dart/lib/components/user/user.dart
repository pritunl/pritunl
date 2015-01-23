library user_comp;

import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWay, NgTwoWay,
  NgCallback;

@Component(
  selector: 'user',
  templateUrl: 'packages/pritunl/components/user/user.html',
  cssUrl: 'packages/pritunl/components/user/user.css'
)
class UserComp {
  @NgOneWay('model')
  user.User model;

  @NgOneWay('show-hidden')
  bool showHidden;

  @NgTwoWay('selected')
  bool selected;

  @NgTwoWay('show-servers')
  bool showServers;
}
