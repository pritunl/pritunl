library user_mod;

import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:async' as async;

@Injectable()
class User extends mdl.Model {
  bool showServers;

  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('organization')
  String organization;

  @mdl.Validator('organization')
  void organizationValidator(val) {
    if (val == null || val == '') {
      throw new mdl.Invalid('empty', 'Organization cannot be empty');
    }
  }

  @mdl.Attribute('organization_name')
  String organizationName;

  @mdl.Attribute('name')
  String name;

  @mdl.Validator('name')
  void nameValidator(val) {
    if (val == null || val == '') {
      throw new mdl.Invalid('empty', 'User name cannot be empty');
    }
  }

  @mdl.Attribute('email')
  String email;

  @mdl.Validator('email')
  void emailValidator(val) {
    if (val != null && val != '' && !val.contains('@')) {
      throw new mdl.Invalid('empty', 'User email is invalid');
    }
  }

  @mdl.Attribute('type')
  String type;

  @mdl.Attribute('otp_auth')
  bool otpAuth;

  @mdl.Attribute('otp_secret')
  String otpSecret;

  @mdl.Attribute('disabled')
  bool disabled;

  @mdl.Attribute('servers')
  List<Map<String, dynamic>> servers;

  @mdl.Attribute('status')
  bool status;

  @mdl.Attribute('send_key_email')
  String _sendKeyEmail;

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

  void init() {
    this.showServers = false;
  }

  async.Future genNewOtp() {
    return this.send('put', this.url + '/otp_secret', null);
  }

  async.Future mailKey() {
    var clone = this.clone();
    clone._sendKeyEmail = utils.getDomain();
    return clone.save(['send_key_email']);
  }
}
