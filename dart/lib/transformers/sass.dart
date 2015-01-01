library sass;

import 'package:barback/barback.dart' as barback;
import 'dart:async' as async;
import 'dart:io' as io;
import 'dart:convert' as conv;

class SassError implements Exception {
  var output;

  SassError(this.output);

  toString() => output;
}

class SassTran extends barback.Transformer {
  SassTran.asPlugin();

  isPrimary(id) {
    return new async.Future.value(id.extension == '.scss');
  }

  convert(content) {
    return io.Process.start('scss', ['-I', 'lib']).then((process) {
      var stdout = new StringBuffer();
      var stderr = new StringBuffer();

      process.stdin.write(content);
      process.stdin.writeln();
      process.stdin.writeln();
      process.stdin.close();

      process.stdout.transform(conv.UTF8.decoder).listen(
          (x) => stdout.write(x));
      process.stderr.transform(conv.UTF8.decoder).listen(
          (x) => stderr.write(x));

      return process.exitCode.then((exitCode) {
        if (exitCode == 0) {
          return stdout.toString();
        } else {
          var output;

          if (stderr.length != 0) {
            output = stderr.toString();
          }
          else {
            output = stdout.toString();
          }

          throw new SassError(output);
        }
      });
    }).catchError((io.ProcessException error) {
      throw new SassError(error.toString());
    }, test: (e) => e is io.ProcessException);
  }

  apply(transform) {
    return transform.primaryInput.readAsString().then((content) {
      var newId = transform.primaryInput.id.changeExtension('.css');

      return this.convert(content).then((newContent) {
        transform.addOutput(new barback.Asset.fromString(newId, newContent));
      });
    });
  }
}
