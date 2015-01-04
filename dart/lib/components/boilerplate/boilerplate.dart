library boilerplate;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'boilerplate',
  templateUrl: 'packages/pritunl/components/boilerplate/boilerplate.html',
  cssUrl: 'packages/pritunl/components/boilerplate/boilerplate.css'
)
class BoilerplateComp {
  BoilerplateComp() {
  }
}
