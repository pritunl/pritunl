library boilerplate_comp;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'x-boilerplate',
  templateUrl: 'packages/pritunl/components/boilerplate/boilerplate.html',
  cssUrl: 'packages/pritunl/components/boilerplate/boilerplate.css'
)
class BoilerplateComp {
  BoilerplateComp() {
  }

  void set scope(ng.Scope scope) {
    // Change detection
    ng.Watch watch = scope.watch('showHidden', (value, previousValue) {
      //print('showHidden: $showHidden');
    });

    // Event listner
    async.Stream stream = scope.on('test-event');
    stream.listen((ng.ScopeEvent evt) {
      print('evt: ${evt.data}');
    });
  }

  var _scope;
  void set scope(ng.Scope scope) {
    this._scope = scope;
  }
  ng.Scope get scope {
    return this._scope;
  }

  void sendEvt() {
    // Go upwards up scope
    this.scope.emit('test-event', 'emit');

    // Go downwards down scope
    this.scope.broadcast('test-event', 'emit');
    print('test');
  }
}
