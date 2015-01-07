library user;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'user',
  templateUrl: 'packages/pritunl/components/user/user.html',
  cssUrl: 'packages/pritunl/components/user/user.css'
)
class UserComp {
  @NgTwoWay('model')
  var model;
}
