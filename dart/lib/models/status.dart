library status;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Status extends model.Model {
  @model.Attr('org_count')
  var orgCount;

  @model.Attr('users_online')
  var usersOnline;

  @model.Attr('user_count')
  var userCount;

  @model.Attr('servers_online')
  var serversOnline;

  @model.Attr('server_count')
  var serverCount;

  @model.Attr('hosts_online')
  var hostsOnline;

  @model.Attr('host_count')
  var hostCount;

  @model.Attr('server_version')
  var serverVersion;

  @model.Attr('current_host')
  var currentHost;

  @model.Attr('public_ip')
  var publicIp;

  @model.Attr('local_networks')
  var localNetworks;

  @model.Attr('notification')
  var notification;

  get url {
    return '/status';
  }

  Status(ng.Http http) : super(http);
}
