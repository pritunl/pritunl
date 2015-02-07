library server_comp;

import 'package:pritunl/models/server.dart' as svr;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;

@Component(
  selector: 'server',
  templateUrl: 'packages/pritunl/components/server/server.html',
  cssUrl: 'packages/pritunl/components/server/server.css'
)
class ServerComp {
  @NgOneWayOneTime('model')
  svr.Server model;
  bool showHidden;

  void toggleHidden() {
    this.showHidden = this.showHidden != true;
  }
}
