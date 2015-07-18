library builder_serv;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:async' as async;

@Injectable()
class BuilderServ {
  ng.Compiler _compiler;
  ng.DirectiveInjector _injector;
  ng.Scope _scope;
  ng.DirectiveMap _directives;

  BuilderServ(this._compiler, this._directives, this._scope, this._injector);

  dom.Element build(selector) {
    var element = dom.document.createElement(selector);
    var template = this._compiler([element], this._directives);

    var childScope = this._scope.createProtoChild();
    var newView = template(childScope, this._injector);
    newView.nodes.forEach((node) => element.append(node));
    async.Timer.run(() => childScope.apply());

    return element;
  }
}
