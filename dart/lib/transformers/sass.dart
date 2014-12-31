library sass;

import 'package:barback/barback.dart' as barback;
import 'dart:async' as async;

class SassTran extends barback.Transformer {
  SassTran.asPlugin();

  isPrimary(id) {
    return new async.Future.value(id.extension == '.sass');
  }

  apply(transform) {
    return transform.primaryInput.readAsString().then((content) {
      var newId = transform.primaryInput.id.changeExtension('.css');
      var newContent = 'test\n$content';
      transform.addOutput(new barback.Asset.fromString(newId, newContent));
    });
  }
}
