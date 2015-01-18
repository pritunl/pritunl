library checkbox_comp;

import 'package:angular/angular.dart' show Component, NgTwoWay;

@Component(
  selector: 'checkbox',
  template: '<div ng-click="onClick()">'
    '<glyphicon type="ok" ng-if="state"></glyphicon></div>',
  cssUrl: 'packages/pritunl/components/checkbox/checkbox.css'
)
class CheckboxComp {
  @NgTwoWay('state')
  bool state;

  void onClick() {
    this.state = this.state != true;
  }
}
