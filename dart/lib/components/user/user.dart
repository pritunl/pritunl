library user;

import 'package:angular/angular.dart' show Component, NgAttr, NgTwoWay;

@Component(
  selector: 'user',
  templateUrl: 'packages/pritunl/components/user/user.html',
  cssUrl: 'packages/pritunl/components/user/user.css'
)
class UserComp {
  @NgTwoWay('model')
  var model;

  @NgTwoWay('collection')
  var collection;

  @NgAttr('selected')
  var selected;
}
