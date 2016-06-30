library status_mod;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Status extends mdl.Model {
  @mdl.Attribute('org_count')
  int orgCount;

  @mdl.Attribute('users_online')
  int usersOnline;

  @mdl.Attribute('user_count')
  int userCount;

  @mdl.Attribute('servers_online')
  int serversOnline;

  @mdl.Attribute('server_count')
  int serverCount;

  @mdl.Attribute('hosts_online')
  int hostsOnline;

  @mdl.Attribute('host_count')
  int hostCount;

  @mdl.Attribute('server_version')
  String serverVersion;

  @mdl.Attribute('current_host')
  String currentHost;

  @mdl.Attribute('public_ip')
  String publicIp;

  @mdl.Attribute('local_networks')
  List<String> localNetworks;

  @mdl.Attribute('notification')
  String notification;

  Status(ng.Http http) : super(http);

  String get url {
    return '/status';
  }
}
