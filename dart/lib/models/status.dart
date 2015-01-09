library status;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Status extends model.Model {
  var org_count;
  var users_online;
  var user_count;
  var servers_online;
  var server_count;
  var hosts_online;
  var host_count;
  var server_version;
  var current_host;
  var public_ip;
  var local_networks;
  var notification;

  get url {
    return '/status';
  }

  Status(ng.Http http) : super(http);
}
