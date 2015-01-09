library container;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'container',
  template: '<div class="container"><content></content></div>',
  cssUrl: 'packages/pritunl/components/container/container.css'
)
class ContainerComp {
}
