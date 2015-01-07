library users;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'users',
  templateUrl: 'packages/pritunl/components/users/users.html',
  cssUrl: 'packages/pritunl/components/users/users.css'
)
class UsersComp implements ng.AttachAware {
  var http;
  var users;

  @NgTwoWay('org-id')
  var orgId;

  UsersComp(ng.Http this.http);

  attach() {
    this.update();
  }

  update() {
    this.http.get('/user/${this.orgId}').then((response) {
      this.users = response.data;
    });
  }
}
