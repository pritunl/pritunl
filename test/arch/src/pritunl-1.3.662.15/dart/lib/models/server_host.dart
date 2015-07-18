library server_host_mod;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class ServerHost extends mdl.Model {
  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('name')
  String name;

  @mdl.Attribute('server')
  String server;

  @mdl.Attribute('status')
  String status;

  @mdl.Attribute('address')
  String address;

  ServerHost(ng.Http http) : super(http);

  String get url {
    var url = '/server/${this.server}/host';

    if (this.id != null) {
      url += '/${this.id}';
    }

    return url;
  }
}
