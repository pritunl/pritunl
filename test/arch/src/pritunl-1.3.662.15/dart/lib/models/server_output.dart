library server_output_mod;

import 'package:pritunl/model.dart' as mdl;
import 'package:pritunl/models/server.dart' as svr;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class ServerOutput extends mdl.Model {
  svr.Server server;

  @mdl.Attribute('output')
  List<String> output;

  ServerOutput(ng.Http http, this.server) : super(http);

  String get url {
    return '/server/${this.server.id}/output';
  }
}
