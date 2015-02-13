library server_mod;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class Server extends mdl.Model {
  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('name')
  String name;

  @mdl.Attribute('server')
  String server;

  Server(ng.Http http) : super(http);

  String get url {
    var url = '/server/${this.server}/organization';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }
}
