library server_hosts_col;

import 'package:pritunl/collection.dart' as collec;
import 'package:pritunl/models/server.dart' as svr;
import 'package:pritunl/models/server_host.dart' as svr_hst;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class ServerHosts extends collec.Collection {
  Type model = svr_hst.ServerHost;
  svr.Server server;

  ServerHosts(ng.Http http, this.server) : super(http);

  String get url {
    return '/server/${this.server.id}/host';
  }
}
