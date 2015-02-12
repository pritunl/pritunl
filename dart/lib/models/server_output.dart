library server_output_mod;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class ServerOutput extends mdl.Model {
  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('output')
  List<String> output;

  ServerOutput(ng.Http http) : super(http);

  String get url {
    return '/server/${this.id}/output';
  }
}
