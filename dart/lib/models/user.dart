library user;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class User extends model.Model {
  @model.Attr('id')
  var id;

  @model.Attr('organization')
  var organization;

  @model.Attr('organization_name')
  var organizationName;

  @model.Attr('name')
  var name;

  @model.Attr('email')
  var email;

  @model.Attr('type')
  var type;

  @model.Attr('otp_auth')
  var otpAuth;

  @model.Attr('otp_secret')
  var otpSecret;

  @model.Attr('disabled')
  var disabled;

  @model.Attr('servers')
  var servers;

  @model.Attr('status')
  var status;

  get url {
    return '/user/${this.organization}/${this.id}';
  }

  User(ng.Http http) : super(http);
}
