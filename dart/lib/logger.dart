library logger;

import 'package:logging/logging.dart' as logging;

logging.Logger log = new logging.Logger('pritunl');

void setup() {
  logging.Logger.root.level = logging.Level.ALL;
  logging.Logger.root.onRecord.listen((logging.LogRecord rec) {
    print('${rec.level.name}: ${rec.time}: ${rec.message}');
  });
}

void config(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.config(message, error, stackTrace);
}

void fine(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.fine(message, error, stackTrace);
}

void finer(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.finer(message, error, stackTrace);
}

void finest(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.finest(message, error, stackTrace);
}

void info(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.config(message, error, stackTrace);
}

void severe(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.severe(message, error, stackTrace);
}

void shout(message, [Object error, StackTrace stackTrace]) {
  logging.Logger.root.shout(message, error, stackTrace);
}
