library logger;

import 'package:logging/logging.dart' as logging;

logging.Logger log = new logging.Logger('pritunl');

void setup() {
  log.level = logging.Level.ALL;
  log.onRecord.listen((logging.LogRecord rec) {
    print('${rec.level.name}: ${rec.time}: ${rec.message}');
  });
}

void config(message, [Object error, StackTrace stackTrace]) {
  log.config(message, error, stackTrace);
}

void fine(message, [Object error, StackTrace stackTrace]) {
  log.fine(message, error, stackTrace);
}

void finer(message, [Object error, StackTrace stackTrace]) {
  log.finer(message, error, stackTrace);
}

void finest(message, [Object error, StackTrace stackTrace]) {
  log.finest(message, error, stackTrace);
}

void info(message, [Object error, StackTrace stackTrace]) {
  log.config(message, error, stackTrace);
}

void severe(message, [Object error, StackTrace stackTrace]) {
  log.severe(message, error, stackTrace);
}

void shout(message, [Object error, StackTrace stackTrace]) {
  log.shout(message, error, stackTrace);
}
