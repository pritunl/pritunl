library btn;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'btn',
  template: '<button type="button" ng-class="btnType">'
    '<content></content></button>',
  cssUrl: 'packages/pritunl/components/btn/btn.css'
)
class BtnComp {
  @NgAttr('btn-type')
  var btnType;
}
