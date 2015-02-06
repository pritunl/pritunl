library logger;

import 'package:pritunl/utils/utils.dart' as utils;

import 'package:logging/logging.dart' as logging;

void setup() {
  logging.Logger.root.level = logging.Level.FINE;
  logging.Logger.root.onRecord.listen((logging.LogRecord rec) {
    var color;

    if (rec.level.value <= 500) {
      color = '#bdbdbd'; // Debug
    }
    else if (rec.level.value <= 800) {
      color = '#31b0d5'; // Info
    }
    else if (rec.level.value <= 900) {
      color = '#f0ad4e'; // Warning
    }
    else if (rec.level.value <= 1000) {
      color = '#d9534f'; // Error
    }
    else if (rec.level.value <= 1200) {
      color = '#d9534f'; // Critical
    }

    utils.printColor('${rec.level.name}:${rec.time}: ${rec.message}', color);

    if (rec.error != null) {
      utils.printColor('  TYPE: ${rec.error}', color);
    }

    if (rec.stackTrace != null) {
      var stackTrace = '';
      rec.stackTrace.toString().split('\n').forEach((line) {
        stackTrace += '  $line\n';
      });
      utils.printColor(stackTrace, '#d9534f');
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
