library pritunl;

import 'package:pritunl/routers/routers.dart' as routers;
import 'package:pritunl/components/components.dart' as components;
import 'package:pritunl/decorators/decorators.dart' as decorators;
import 'package:pritunl/formatters/formatters.dart' as formatters;

import 'package:angular/application_factory.dart' as appfactory;

void main() {
  appfactory.applicationFactory()
    .addModule(new routers.RoutersMod())
    .addModule(new components.ComponentsMod())
    .addModule(new decorators.DecoratorsMod())
    .addModule(new formatters.FormattersMod())
    .run();
}
