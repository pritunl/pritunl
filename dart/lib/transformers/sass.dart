library sass;

import 'package:barback/barback.dart' as barback;
import 'dart:io' as io;
import 'dart:convert' as conv;

var files = new Set();
var touched = {};
var imports = {};

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

addAllPaths(touch, path) {
  if (imports[path] == null) {
    imports[path] = new Set();
  }

  imports[path].toList().forEach((p) {
    touch.add(p);
    addAllPaths(touch, p);
  });
}

class SassError implements Exception {
  var output;

  SassError(this.output);

  toString() => output;
}

class SassTran extends barback.Transformer {
  SassTran.asPlugin();

  get allowedExtensions => '.scss';

  apply(transform) {
    return transform.primaryInput.readAsString().then((content) {
      var curPath = transform.primaryInput.id.path;
      var newId = transform.primaryInput.id.changeExtension('.css');
      files.add(curPath);

      var touch = new Set();

      var re = new RegExp(r"@import '(.*?)';");
      for (var match in re.allMatches(content)) {
        var path = 'lib/${match.group(1)}';

        if (imports[path] == null) {
          imports[path] = new Set();
        }
        imports[path].add(curPath);
      }

      if (touched[curPath] == null) {
        touched[curPath] = 0;
      }
      else if (touched[curPath] > 0) {
        touched[curPath] -= 1;
      }
      else {
        if (imports[curPath] == null) {
          imports[curPath] = new Set();
        }

        imports[curPath].toList().forEach((path) {
          touch.addAll(imports[curPath]);
        });

        addAllPaths(touch, curPath);

        var touchList = touch.toList();
        touchList.forEach((path) {
          if (path != curPath) {
            touched[path] += 1;
          }
        });
        touchList.forEach((path) {
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
