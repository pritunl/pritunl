ace.define('ace/mode/log_highlight_rules', ['require', 'exports', 'module', 'ace/lib/oop', 'ace/mode/text_highlight_rules'], function(require, exports, module) {
'use strict';

var oop = require('../lib/oop');
var TextHighlightRules = require('./text_highlight_rules').TextHighlightRules;

var LogHighlightRules = function() {
  var ws = '(\\s+)';
  var weekday = '((?:Tues|Thur|Thurs|Sun|Mon|Tue|Wed|Thu|Fri|Sat))';
  var month = '((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))';
  var day = '((?:(?:[0-2]?\\d{1})|(?:[3][01]{1})))(?![\\d])';
  var timestamp = '((?:(?:[0-1][0-9])|(?:[2][0-3])|(?:[0-9])):(?:[0-5][0-9])(?::[0-5][0-9])?)';
  var datestamp = '((?:[0-9][0-9][0-9][0-9])-(?:[0-9][0-9])-(?:[0-9][0-9])?)';
  var year = '((?:(?:[1]{1}\\d{1}\\d{1}\\d{1})|(?:[2]{1}\\d{3})))(?![\\d])';

  this.$rules = {
    start: [
      {
        token: 'comment.bold',
        regex: '^(\\[)(.*?)(\\])'
      }, {
        token: 'keyword.bold',
        regex: ws + weekday + ws + month + ws + day + ws + timestamp + ws + year + ws
      }, {
        token: 'keyword.bold',
        regex: ws + datestamp + ws + timestamp + ws
      }, {
        token: 'variable.bold',
        regex: '((?:WARNING)(.*?))$'
      }, {
        token: 'invalid.illegal.bold',
        regex: '((?:ERROR|TLS Error|TLS_ERROR|VERIFY ERROR|OSError)(.*?))$'
      }
    ]
  };
};

oop.inherits(LogHighlightRules, TextHighlightRules);

exports.LogHighlightRules = LogHighlightRules;
});

ace.define('ace/mode/log', ['require', 'exports', 'module', 'ace/lib/oop', 'ace/mode/text', 'ace/mode/text_highlight_rules', 'ace/mode/log_highlight_rules'], function(require, exports, module) {
'use strict';

var oop = require('../lib/oop');
var TextMode = require('./text').Mode;
var TextHighlightRules = require('./text_highlight_rules').TextHighlightRules;
var LogHighlightRules = require('./log_highlight_rules').LogHighlightRules;

var Mode = function(suppressHighlighting) {
  if (suppressHighlighting) {
    this.HighlightRules = TextHighlightRules;
  }
  else {
    this.HighlightRules = LogHighlightRules;
  }
};
oop.inherits(Mode, TextMode);

(function() {
  this.$id = 'ace/mode/log';
}).call(Mode.prototype);

exports.Mode = Mode;
});
