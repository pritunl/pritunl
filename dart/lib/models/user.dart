library user;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class User extends model.Model {
  @model.Attribute('id')
  var id;

  @model.Attribute('organization')
  var organization;

  @model.Attribute('organization_name')
  var organizationName;

  @model.Attribute('name')
  var name;

  @model.Attribute('email')
  var email;

  @model.Attribute('type')
  var type;

  @model.Attribute('otp_auth')
  var otpAuth;

  @model.Attribute('otp_secret')
  var otpSecret;

  @model.Attribute('disabled')
  var disabled;

  @model.Attribute('servers')
  var servers;

  @model.Attribute('status')
  var status;

  get url {
    return '/user/${this.organization}/${this.id}';
  }

  User(ng.Http http) : super(http);
}
