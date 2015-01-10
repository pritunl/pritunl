library user;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class User extends model.Model {
  var id;
  var organization;
  var organization_name;
  var name;
  var email;
  var type;
  var otp_auth;
  var otp_secret;
  var disabled;
  var servers;
  var status;

  get url {
    return '/user/${this.organization}/${this.id}';
  }

  User(ng.Http http) : super(http);
}
