library status;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Status extends model.Model {
  @model.Attribute('org_count')
  int orgCount;

  @model.Attribute('users_online')
  int usersOnline;

  @model.Attribute('user_count')
  int userCount;

  @model.Attribute('servers_online')
  int serversOnline;

  @model.Attribute('server_count')
  int serverCount;

  @model.Attribute('hosts_online')
  int hostsOnline;

  @model.Attribute('host_count')
  int hostCount;

  @model.Attribute('server_version')
  String serverVersion;

  @model.Attribute('current_host')
  String currentHost;

  @model.Attribute('public_ip')
  String publicIp;

  @model.Attribute('local_networks')
  List<String> localNetworks;

  @model.Attribute('notification')
  String notification;

  String get url {
    return '/status';
  }

  Status(ng.Http http) : super(http);
}
