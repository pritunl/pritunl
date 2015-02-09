library server_mod;

import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Server extends mdl.Model {
  usrs.Users users;

  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('name')
  String name;

  @mdl.Validator('name')
  void nameValidator(val) {
    if (val == null || val == '') {
      throw new mdl.Invalid('empty', 'Server name cannot be empty');
    }
  }

  @mdl.Attribute('status')
  String status;

  @mdl.Attribute('uptime')
  int uptime;

  @mdl.Attribute('user_count')
  int user_count;

  @mdl.Attribute('users_online')
  int users_online;

  @mdl.Attribute('devices_online')
  int devices_online;

  @mdl.Attribute('network')
  String network;

  @mdl.Attribute('bind_address')
  String bind_address;

  @mdl.Attribute('port')
  int port;

  @mdl.Attribute('protocol')
  String protocol;

  @mdl.Attribute('dh_param_bits')
  int dh_param_bits;

  @mdl.Attribute('mode')
  String mode;

  @mdl.Attribute('multi_device')
  bool multi_device;

  @mdl.Attribute('local_networks')
  List<String> local_networks;

  @mdl.Attribute('dns_servers')
  List<String> dns_servers;

  @mdl.Attribute('search_domain')
  String search_domain;

  @mdl.Attribute('otp_auth')
  bool otp_auth;

  @mdl.Attribute('cipher')
  String cipher;

  @mdl.Attribute('jumbo_frames')
  bool jumbo_frames;

  @mdl.Attribute('lzo_compression')
  bool lzo_compression;

  @mdl.Attribute('debug')
  bool debug;

  Server(ng.Http http) : super(http);

  String get url {
    var url = '/server';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }
}
