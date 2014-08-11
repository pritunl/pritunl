(function() {
  'use strict';
  if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function (searchElement /*, fromIndex */ ) {
      /*jshint eqeqeq:false, bitwise:false */
      if (this === null) {
        throw new TypeError();
      }
      var t = Object(this);
      var len = t.length >>> 0;
      if (len === 0) {
        return -1;
      }
      var n = 0;
      if (arguments.length > 1) {
        n = Number(arguments[1]);
        if (n != n) { // shortcut for verifying if it's NaN
          n = 0;
        } else if (n !== 0 && n != Infinity && n != -Infinity) {
          n = (n > 0 || -1) * Math.floor(Math.abs(n));
        }
      }
      if (n >= len) {
        return -1;
      }
      var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
      for (; k < len; k++) {
        if (k in t && t[k] === searchElement) {
          return k;
        }
      }
      return -1;
    };
  }

  if (!Function.prototype.bind) {
    Function.prototype.bind = function (oThis) {
      if (typeof this !== 'function') {
        // closest thing possible to the ECMAScript 5 internal
        // IsCallable function
        throw new TypeError('Function.prototype.bind - what is ' +
          'trying to be bound is not callable');
      }

      var aArgs = Array.prototype.slice.call(arguments, 1),
          fToBind = this,
          NOP = function () {},
          Bound = function () {
            return fToBind.apply(this instanceof NOP && oThis ? this : oThis,
              aArgs.concat(Array.prototype.slice.call(arguments)));
          };

      NOP.prototype = this.prototype;
      Bound.prototype = new NOP();

      return Bound;
    };
  }
}());

require.config({
  waitSeconds: 10,
  paths: {
    ace: 'vendor/ace/ace',
    aceModeSh: 'vendor/ace/mode-sh',
    aceModeText: 'vendor/ace/mode-text',
    aceThemeAmbiance: 'vendor/ace/theme-ambiance',
    aceThemeChrome: 'vendor/ace/theme-chrome',
    aceThemeGithub: 'vendor/ace/theme-github',
    aceThemeMonokai: 'vendor/ace/theme-monokai',
    aceThemeTwilight: 'vendor/ace/theme-twilight',
    backbone: 'vendor/backbone/backbone',
    bootstrap: 'vendor/bootstrap/bootstrap',
    d3: 'vendor/d3/d3',
    jquery: 'vendor/jquery/jquery',
    less: 'vendor/less/less',
    qrcode: 'vendor/qrcode/qrcode',
    rickshaw: 'vendor/rickshaw/rickshaw',
    select: 'vendor/select/select',
    sjcl: 'vendor/sjcl/sjcl.min',
    text: 'vendor/requireText/text',
    underscore: 'vendor/underscore/underscore',
    initialize: 'init/testing'
  },
  shim: {
    ace: {exports: 'ace'},
    aceModeSh: ['ace'],
    aceModeText: ['ace'],
    aceThemeAmbiance: ['ace'],
    aceThemeChrome: ['ace'],
    aceThemeGithub: ['ace'],
    aceThemeMonokai: ['ace'],
    aceThemeTwilight: ['ace'],
    backbone: ['less'],
    bootstrap: ['jquery'],
    d3: {exports: 'd3'},
    rickshaw: {deps: ['d3'], exports: 'Rickshaw'},
    sjcl: {exports: 'sjcl'},
    qrcode: {exports: 'QRCode'}
  }
});

require([
  'backbone',
], function(Backbone) {
  'use strict';
  Backbone.View = Backbone.View.extend({
    deinitialize: function() {
    },
    addView: function(view) {
      this.children = this.children || {};
      var id = view.cid;
      this.children[id] = view;
      this.listenToOnce(view, 'destroy', function() {
        this.children[id] = null;
      }.bind(this));
    },
    destroy: function() {
      this.deinitialize();
      if (this.children) {
        for (var id in this.children) {
          if (this.children[id]) {
            this.children[id].destroy();
          }
        }
      }
      this.remove();
      this.trigger('destroy');
    }
  });
});

require([
  'jquery',
  'underscore',
  'backbone',
  'models/subscription',
  'collections/event',
  'views/header',
  'routers/main',
  'initialize'
], function($, _, Backbone, SubscriptionModel, EventCollection, HeaderView,
    mainRouter, initialize) {
  'use strict';

  initialize();

  window.formatUptime = function(time) {
    var days = Math.floor(time / 86400);
    time -= days * 86400;
    var hours = Math.floor(time / 3600);
    time -= hours * 3600;
    var minutes = Math.floor(time / 60);
    time -= minutes * 60;
    var seconds = time;
    return days + 'd ' + hours + 'h ' + minutes + 'm ' + seconds + 's';
  };

  window.formatTime = function(time, type) {
    var abbrev = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var date = new Date(0);
    var curDate = new Date();
    time = time * 1000;
    date.setUTCMilliseconds(parseInt(time, 10));
    var month = abbrev[date.getMonth()];
    var day = date.getDate().toString();
    var year = date.getFullYear().toString();
    var hours = date.getHours();
    var meridiem;
    if (hours > 12) {
      hours = (hours - 12).toString();
      meridiem = 'pm';
    }
    else {
      hours = hours.toString();
      meridiem = 'am';
    }
    if (hours === '0') {
      hours = '12';
    }
    var minutes = date.getMinutes().toString();
    if (minutes.length < 2) {
      minutes = '0' + minutes;
    }
    if (type === 'short') {
      if (curDate.getDate() === date.getDate() &&
          curDate.getMonth() === date.getMonth() &&
          curDate.getFullYear() === date.getFullYear()) {
        time = hours + ':' + minutes + ' ' + meridiem;
      }
      else {
        time = month + ' ' + day;
        if (curDate.getFullYear() !== date.getFullYear()) {
          time += ' ' + year;
        }
      }
    }
    else if (type === 'date') {
      time = month + ' ' + day;
    }
    else {
      time = hours + ':' + minutes + ' ' + meridiem + ' - ' +
        month + ' ' + day + ' ' + year;
    }

    return time;
  };

  window.formatSize = function(bytes, decimals) {
    if (decimals === undefined) {
      decimals = 1;
    }
    if (!bytes) {
      bytes = '0 bytes';
    }
    else if (bytes < 1024) {
      bytes = bytes + ' bytes';
    }
    else if (bytes < 1048576) {
      bytes = Math.round(bytes / 1024).toFixed(decimals) + ' kB';
    }
    else if (bytes < 1073741824) {
      bytes = (bytes / 1048576).toFixed(decimals) + ' MB';
    }
    else if (bytes < 1099511627776) {
      bytes = (bytes / 1073741824).toFixed(decimals) + ' GB';
    }
    else {
      bytes = (bytes / 1099511627776).toFixed(decimals) + ' TB';
    }

    return bytes;
  };

  $.getCachedScript = function(url, options) {
    options = $.extend(options || {}, {
      dataType: 'script',
      cache: true,
      url: url
    });
    return $.ajax(options);
  };

  var append = $.fn.append;
  $.fn.append = function() {
    if (this[0].className === 'alerts-container' &&
        $(this).children().length > 2) {
      $(this).children().first().find('.close').click();
    }
    return append.apply(this, arguments);
  };

  $.fn.roll = function(timeout, complete) {
    var timer;

    var rotate = function(degree) {
      $(this).css('-webkit-transform', 'rotate(' + degree + 'deg)');
      $(this).css('-moz-transform', 'rotate(' + degree + 'deg)');
      $(this).css('-ms-transform', 'rotate(' + degree + 'deg)');
      $(this).css('-o-transform', 'rotate(' + degree + 'deg)');
      $(this).css('transform', 'rotate(' + degree + 'deg)');

      timer = setTimeout(function() {
        degree += 1;
        rotate(degree);
      }, 4);
    }.bind(this);

    rotate(0);

    setTimeout(function() {
      clearTimeout(timer);

      $(this).css('-webkit-transform', 'rotate(0deg)');
      $(this).css('-moz-transform', 'rotate(0deg)');
      $(this).css('-ms-transform', 'rotate(0deg)');
      $(this).css('-o-transform', 'rotate(0deg)');
      $(this).css('transform', 'rotate(0deg)');

      if (complete) {
        complete();
      }
    }.bind(this), timeout);
  };

  $(document).on('dblclick mousedown', '.no-select', false);

  var init = function() {
    window.events = new EventCollection();
    window.events.start();

    var headerView = new HeaderView();
    $('body').prepend(headerView.render().el);

    mainRouter.initialize();
  };

  var model = new SubscriptionModel();
  model.fetch({
    url: '/subscription/state',
    success: function(model) {
      window.enterprise = model.get('active');
      if (window.enterprise) {
        $('body').addClass('enterprise');
      }
      init();
    },
    error: function() {
      init();
    }
  });
});
