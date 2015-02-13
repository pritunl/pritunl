library organizations_col;

import 'package:pritunl/collection.dart' as collec;
import 'package:pritunl/models/server_org.dart' as svr_org;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class ServerOrgs extends collec.Collection {
  Type model = svr_org.ServerOrg;
  String server;

  ServerOrgs(ng.Http http, this.server) : super(http);

  String get url {
    return '/server/${this.server}/organization';
  }
}
