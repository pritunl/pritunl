library logger;

import 'package:logging/logging.dart' as logging;

void setup() {
  logging.Logger.root.level = logging.Level.FINE;
  logging.Logger.root.onRecord.listen((logging.LogRecord rec) {
    print('${rec.level.name}: ${rec.time}: ${rec.message}');

    if (rec.error != null) {
      print('  TYPE: ${rec.error}');
    }

    if (rec.stackTrace != null) {
      var stackTrace = '';
      rec.stackTrace.toString().split('\n').forEach((line) {
        stackTrace += '  $line\n';
      });
      print(stackTrace);
    }
  });
}

// Debug
void finest(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.finest(message, error, stackTrace);
}

// Debug
void finer(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.finer(message, error, stackTrace);
}

// Debug
void fine(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.fine(message, error, stackTrace);
}

// Debug
void config(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.config(message, error, stackTrace);
}

// Info
void info(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.config(message, error, stackTrace);
}

// Warning
void warning(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.warning(message, error, stackTrace);
}

// Error
void severe(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.severe(message, error, stackTrace);
}

// Critical
void shout(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.shout(message, error, stackTrace);
}
