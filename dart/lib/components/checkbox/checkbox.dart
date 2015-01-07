library checkbox;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'checkbox',
  template: '<div ng-click="onClick()">'
    '<glyphicon type="ok" ng-if="state"></glyphicon></div>',
  cssUrl: 'packages/pritunl/components/checkbox/checkbox.css'
)
class CheckboxComp {
  @NgTwoWay('state')
  var state;

  onClick() {
    this.state = this.state != true;
  }
}
