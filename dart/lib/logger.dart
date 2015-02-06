library logger;

import 'package:logging/logging.dart' as logging;

import 'dart:js' as js;

void setup() {
  logging.Logger.root.level = logging.Level.FINE;
  logging.Logger.root.onRecord.listen((logging.LogRecord rec) {
    var color;

    if (rec.level.value <= 500) {
      color = 'gray'; // Debug
    } else if (rec.level.value <= 800) {
      color = 'blue'; // Info
    } else if (rec.level.value <= 900) {
      color = 'yellow'; // Warning
    } else if (rec.level.value <= 1000) {
      color = 'red'; // Error
    } else if (rec.level.value <= 1200) {
      color = 'red'; // Critical
    }

    js.context['console'].callMethod('log', [
      '%c${rec.level.name}: ${rec.time}: ${rec.message}', 'color: $color']);

    if (rec.error != null) {
      js.context['console'].callMethod('log', [
        '%c  TYPE: ${rec.error}', 'color: $color']);
    }

    if (rec.stackTrace != null) {
      var stackTrace = '';
      rec.stackTrace.toString().split('\n').forEach((line) {
        stackTrace += '  $line\n';
      });
      js.context['console'].callMethod('log', [
        '%c$stackTrace', 'color: red']);
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
