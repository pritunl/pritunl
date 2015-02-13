library server_comp;

import 'package:pritunl/models/server.dart' as svr;
import 'package:pritunl/alert.dart' as alrt;
import 'package:pritunl/logger.dart' as logger;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'server',
  templateUrl: 'packages/pritunl/components/server/server.html',
  cssUrl: 'packages/pritunl/components/server/server.css'
)
class ServerComp implements ng.AttachAware {
  bool showHidden;

  @NgOneWayOneTime('model')
  svr.Server model;

  void toggleHidden() {
    this.showHidden = this.showHidden != true;
  }

  void attach() {
    this.model.output.fetch().then((_) {
      print(this.model.output.output);
    }).catchError((err) {
      logger.severe('Failed to load server output', err);
      new alrt.Alert('Failed to load server output, server error occurred.',
      'danger');
    });
  }
}
