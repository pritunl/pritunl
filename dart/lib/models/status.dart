library status;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Status extends model.Model {
  @model.Attribute('org_count')
  var orgCount;

  @model.Attribute('users_online')
  var usersOnline;

  @model.Attribute('user_count')
  var userCount;

  @model.Attribute('servers_online')
  var serversOnline;

  @model.Attribute('server_count')
  var serverCount;

  @model.Attribute('hosts_online')
  var hostsOnline;

  @model.Attribute('host_count')
  var hostCount;

  @model.Attribute('server_version')
  var serverVersion;

  @model.Attribute('current_host')
  var currentHost;

  @model.Attribute('public_ip')
  var publicIp;

  @model.Attribute('local_networks')
  var localNetworks;

  @model.Attribute('notification')
  var notification;

  get url {
    return '/status';
  }

  Status(ng.Http http) : super(http);
}
