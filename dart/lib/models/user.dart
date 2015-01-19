library user_mod;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class User extends model.Model {
  @model.Attribute('id')
  String id;

  @model.Attribute('organization')
  String organization;

  @model.Validator('organization')
  void organizationValidator(val) {
    if (val == null || val == '') {
      throw new model.Invalid('empty', 'Organization cannot be empty');
    }
  }

  @model.Attribute('organization_name')
  String organizationName;

  @model.Attribute('name')
  String name;

  @model.Validator('name')
  void nameValidator(val) {
    if (val == null || val == '') {
      throw new model.Invalid('empty', 'User name cannot be empty');
    }
  }

  @model.Attribute('email')
  String email;

  @model.Validator('email')
  void emailValidator(val) {
    if (val != null && val != '' && !val.contains('@')) {
      throw new model.Invalid('empty', 'User email is invalid');
    }
  }

  @model.Attribute('type')
  String type;

  @model.Attribute('otp_auth')
  bool otpAuth;

  @model.Attribute('otp_secret')
  String otpSecret;

  @model.Attribute('disabled')
  bool disabled;

  @model.Attribute('servers')
  List<Map> servers;

  @model.Attribute('status')
  bool status;

  String get url {
    return '/user/${this.organization}/${this.id}';
  }

  User(ng.Http http) : super(http);
}
