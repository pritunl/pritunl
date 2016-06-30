library server_col;

import 'package:pritunl/collection.dart' as collec;
import 'package:pritunl/models/server.dart' as svr;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Servers extends collec.Collection {
  Type model = svr.Server;

  Servers(ng.Http http) : super(http);

  String get url {
    return '/server';
  }
}
