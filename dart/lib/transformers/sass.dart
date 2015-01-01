library sass;

import 'package:barback/barback.dart' as barback;
import 'dart:io' as io;
import 'dart:convert' as conv;

class SassError implements Exception {
  var output;

  SassError(this.output);

  toString() => output;
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

var sassFiles = new Set();
var sassTouched = {};

class SassTran extends barback.Transformer {
  SassTran.asPlugin();

  get allowedExtensions => '.scss';

  apply(transform) {
    return transform.primaryInput.readAsString().then((content) {
      var curPath = transform.primaryInput.id.path;
      var newId = transform.primaryInput.id.changeExtension('.css');
      sassFiles.add(curPath);

      if (sassTouched[curPath] == null) {
        sassTouched[curPath] = 0;
      }
      else if (sassTouched[curPath] > 0) {
        sassTouched[curPath] -= 1;
      }
      else {
        sassFiles.forEach((path) {
          if (path != curPath) {
            sassTouched[path] += 1;
          }
        });
        sassFiles.forEach((path) {
          if (path != curPath) {
            io.Process.start('touch', ['-c', path]);
          }
        });
      }

      return convert(content).then((newContent) {
        transform.addOutput(new barback.Asset.fromString(newId, newContent));
      });
    });
  }
}
