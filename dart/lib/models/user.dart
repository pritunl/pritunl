library user_mod;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:async' as async;

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
  List<Map<String, dynamic>> servers;

  @model.Attribute('status')
  bool status;

  User(ng.Http http) : super(http);

  String get url {
    var url = '/user/${this.organization}';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }

  String get keyUrl {
    var loc = dom.window.location;
    return '${loc.protocol}//${loc.host}/key/${this.organization}'
      '/${this.id}.tar';
  }

  async.Future genNewOtp() {
    return this.send('put', this.url + '/otp_secret', null);
  }
}
