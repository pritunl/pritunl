library server_mod;

import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/collections/server_orgs.dart' as svr_orgs;
import 'package:pritunl/collections/server_hosts.dart' as svr_hsts;
import 'package:pritunl/models/server_output.dart' as svr_otpt;
import 'package:pritunl/models/server_link_output.dart' as svr_lnk_otpt;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:async' as async;

@Injectable()
class Server extends mdl.Model {
  var _count;
  var _curUptime;
  svr_otpt.ServerOutput output;
  svr_lnk_otpt.ServerLinkOutput linkOutput;
  svr_orgs.ServerOrgs orgs;
  svr_hsts.ServerHosts hosts;

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
  int userCount;

  @mdl.Attribute('users_online')
  int usersOnline;

  @mdl.Attribute('devices_online')
  int devicesOnline;

  @mdl.Attribute('network')
  String network;

  @mdl.Attribute('bind_address')
  String bindAddress;

  @mdl.Attribute('port')
  int port;

  @mdl.Attribute('protocol')
  String protocol;

  @mdl.Attribute('dh_param_bits')
  int dhParamBits;

  @mdl.Attribute('mode')
  String mode;

  @mdl.Attribute('multi_device')
  bool multiDevice;

  @mdl.Attribute('local_networks')
  List<String> localNetworks;

  @mdl.Attribute('dns_servers')
  List<String> dnsServers;

  @mdl.Attribute('search_domain')
  String searchDomain;

  @mdl.Attribute('otp_auth')
  bool otpAuth;

  @mdl.Attribute('cipher')
  String cipher;

  @mdl.Attribute('jumbo_frames')
  bool jumboFrames;

  @mdl.Attribute('lzo_compression')
  bool lzoCompression;

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

  void _counter() {
    if (this.uptime == null) {
      this._count = null;
      return;
    }

    if (this.uptime < this._curUptime) {
      this._count = 0;
    }

    this._curUptime = this.uptime;
    this._count += 1;
    new async.Timer(const Duration(seconds: 1), () {
      this._counter();
    });
  }

  int get curUptime {
    if (this.uptime == null) {
      return null;
    }

    if (this._count == null) {
      this._count = 0;
      this._curUptime = this.uptime;
      this._counter();
    }

    return this.uptime + this._count;
  }

  void init() {
    this.output = new svr_otpt.ServerOutput(this.http, this);
    this.linkOutput = new svr_lnk_otpt.ServerLinkOutput(this.http, this);
    this.orgs = new svr_orgs.ServerOrgs(this.http, this);
    this.hosts = new svr_hsts.ServerHosts(this.http, this);
  }

  String get modeLong {
    if (this.mode == 'all_traffic') {
      return 'All Traffic';
    }
    else if (this.mode == 'local_traffic') {
      return 'Local Traffic Only';
    }
    else if (this.mode == 'vpn_traffic') {
      return 'VPN Traffic Only';
    }
    return 'Unknown';
  }

  async.Future start() {
    return this.send('put', this.url + '/start', null);
  }

  async.Future stop() {
    return this.send('put', this.url + '/stop', null);
  }

  async.Future restart() {
    return this.send('put', this.url + '/restart', null);
  }
}
