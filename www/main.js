/* jshint -W069:true */
(function() {
  'use strict';
  window.slideTime = 100;

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
            return fToBind.apply(this instanceof NOP &&
              oThis ? this : oThis,
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
    aceModeLog: 'vendor/ace/mode-log',
    aceModeSh: 'vendor/ace/mode-sh',
    aceModeText: 'vendor/ace/mode-text',
    aceThemePritunl: 'vendor/ace/theme-pritunl',
    backbone: 'vendor/backbone/backbone',
    bootstrap: 'vendor/bootstrap/bootstrap',
    d3: 'vendor/d3/d3',
    jquery: 'vendor/jquery/jquery',
    less: 'vendor/less/less',
    qrcode: 'vendor/qrcode/qrcode',
    rickshaw: 'vendor/rickshaw/rickshaw',
    select: 'vendor/select/select',
    text: 'vendor/requireText/text',
    underscore: 'vendor/underscore/underscore',
    initialize: 'init/testing'
  },
  shim: {
    ace: {exports: 'ace'},
    aceModeLog: ['ace'],
    aceModeSh: ['ace'],
    aceModeText: ['ace'],
    aceThemePritunl: ['ace'],
    backbone: ['less'],
    bootstrap: ['jquery'],
    d3: {exports: 'd3'},
    rickshaw: {deps: ['d3'], exports: 'Rickshaw'},
    qrcode: {exports: 'QRCode'}
  }
});

require([
  'backbone'
], function(Backbone) {
  'use strict';
  Backbone.View = Backbone.View.extend({
    deinitialize: function() {},
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
  'models/state',
  'models/subscription',
  'collections/event',
  'views/header',
  'routers/main',
  'initialize'
], function($, _, Backbone, StateModel, SubscriptionModel, EventCollection,
    HeaderView, mainRouter, initialize) {
  'use strict';

  initialize();

  window.formatUptime = function(time) {
    var days = Math.floor(time / 86400);
    time -= days * 86400;
    var hours = Math.floor(time / 3600);
    time -= hours * 3600;
    var minutes = Math.floor(time / 60);
    time -= minutes * 60;
    return days + 'd ' + hours + 'h ' + minutes + 'm ' + time + 's';
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
      if (curDate.getFullYear() !== date.getFullYear()) {
        time += ' ' + year;
      }
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

  window.uuid = function() {
    var uuid = '';
    for (var i = 0; i < 8; i++) {
      uuid += Math.floor((1 + Math.random()) * 0x10000).toString(
        16).substring(1);
    }
    return uuid;
  };

  window.md5 = function(string) {
    /* jshint -W016:true, -W027:true, -W052:true, -W064:true */
    function RotateLeft(lValue, iShiftBits) {
      return (lValue<<iShiftBits) | (lValue>>>(32-iShiftBits));
    }

    function AddUnsigned(lX,lY) {
      var lX4,lY4,lX8,lY8,lResult;
      lX8 = (lX & 0x80000000);
      lY8 = (lY & 0x80000000);
      lX4 = (lX & 0x40000000);
      lY4 = (lY & 0x40000000);
      lResult = (lX & 0x3FFFFFFF)+(lY & 0x3FFFFFFF);
      if (lX4 & lY4) {
        return (lResult ^ 0x80000000 ^ lX8 ^ lY8);
      }
      if (lX4 | lY4) {
        if (lResult & 0x40000000) {
          return (lResult ^ 0xC0000000 ^ lX8 ^ lY8);
        } else {
          return (lResult ^ 0x40000000 ^ lX8 ^ lY8);
        }
      } else {
        return (lResult ^ lX8 ^ lY8);
      }
    }

    function F(x,y,z) { return (x & y) | ((~x) & z); }
    function G(x,y,z) { return (x & z) | (y & (~z)); }
    function H(x,y,z) { return (x ^ y ^ z); }
    function I(x,y,z) { return (y ^ (x | (~z))); }

    function FF(a,b,c,d,x,s,ac) {
      a = AddUnsigned(a, AddUnsigned(AddUnsigned(F(b, c, d), x), ac));
      return AddUnsigned(RotateLeft(a, s), b);
    }

    function GG(a,b,c,d,x,s,ac) {
      a = AddUnsigned(a, AddUnsigned(AddUnsigned(G(b, c, d), x), ac));
      return AddUnsigned(RotateLeft(a, s), b);
    }

    function HH(a,b,c,d,x,s,ac) {
      a = AddUnsigned(a, AddUnsigned(AddUnsigned(H(b, c, d), x), ac));
      return AddUnsigned(RotateLeft(a, s), b);
    }

    function II(a,b,c,d,x,s,ac) {
      a = AddUnsigned(a, AddUnsigned(AddUnsigned(I(b, c, d), x), ac));
      return AddUnsigned(RotateLeft(a, s), b);
    }

    function ConvertToWordArray(string) {
      var lWordCount;
      var lMessageLength = string.length;
      var lNumberOfWords_temp1=lMessageLength + 8;
      var lNumberOfWords_temp2=(lNumberOfWords_temp1-
        (lNumberOfWords_temp1 % 64))/64;
      var lNumberOfWords = (lNumberOfWords_temp2+1)*16;
      var lWordArray=Array(lNumberOfWords-1);
      var lBytePosition = 0;
      var lByteCount = 0;
      while ( lByteCount < lMessageLength ) {
        lWordCount = (lByteCount-(lByteCount % 4))/4;
        lBytePosition = (lByteCount % 4)*8;
        lWordArray[lWordCount] = (lWordArray[lWordCount] |
          (string.charCodeAt(lByteCount)<<lBytePosition));
        lByteCount++;
      }
      lWordCount = (lByteCount-(lByteCount % 4))/4;
      lBytePosition = (lByteCount % 4)*8;
      lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80<<lBytePosition);
      lWordArray[lNumberOfWords-2] = lMessageLength<<3;
      lWordArray[lNumberOfWords-1] = lMessageLength>>>29;
      return lWordArray;
    }

    function WordToHex(lValue) {
      var WordToHexValue='',WordToHexValue_temp='',lByte,lCount;
      for (lCount = 0;lCount<=3;lCount++) {
        lByte = (lValue>>>(lCount*8)) & 255;
        WordToHexValue_temp = '0' + lByte.toString(16);
        WordToHexValue = WordToHexValue + WordToHexValue_temp.substr(
          WordToHexValue_temp.length-2,2);
      }
      return WordToHexValue;
    }

    function Utf8Encode(string) {
      string = string.replace(/\r\n/g,'\n');
      var utftext = '';

      for (var n = 0; n < string.length; n++) {
        var c = string.charCodeAt(n);

        if (c < 128) {
          utftext += String.fromCharCode(c);
        }
        else if((c > 127) && (c < 2048)) {
          utftext += String.fromCharCode((c >> 6) | 192);
          utftext += String.fromCharCode((c & 63) | 128);
        }
        else {
          utftext += String.fromCharCode((c >> 12) | 224);
          utftext += String.fromCharCode(((c >> 6) & 63) | 128);
          utftext += String.fromCharCode((c & 63) | 128);
        }
      }

      return utftext;
    }

    var x=Array();
    var k,AA,BB,CC,DD,a,b,c,d;
    var S11=7, S12=12, S13=17, S14=22;
    var S21=5, S22=9 , S23=14, S24=20;
    var S31=4, S32=11, S33=16, S34=23;
    var S41=6, S42=10, S43=15, S44=21;

    string = Utf8Encode(string);

    x = ConvertToWordArray(string);

    a = 0x67452301;
    b = 0xEFCDAB89;
    c = 0x98BADCFE;
    d = 0x10325476;

    for (k=0;k<x.length;k+=16) {
      AA=a; BB=b; CC=c; DD=d;
      a=FF(a,b,c,d,x[k+0], S11,0xD76AA478);
      d=FF(d,a,b,c,x[k+1], S12,0xE8C7B756);
      c=FF(c,d,a,b,x[k+2], S13,0x242070DB);
      b=FF(b,c,d,a,x[k+3], S14,0xC1BDCEEE);
      a=FF(a,b,c,d,x[k+4], S11,0xF57C0FAF);
      d=FF(d,a,b,c,x[k+5], S12,0x4787C62A);
      c=FF(c,d,a,b,x[k+6], S13,0xA8304613);
      b=FF(b,c,d,a,x[k+7], S14,0xFD469501);
      a=FF(a,b,c,d,x[k+8], S11,0x698098D8);
      d=FF(d,a,b,c,x[k+9], S12,0x8B44F7AF);
      c=FF(c,d,a,b,x[k+10],S13,0xFFFF5BB1);
      b=FF(b,c,d,a,x[k+11],S14,0x895CD7BE);
      a=FF(a,b,c,d,x[k+12],S11,0x6B901122);
      d=FF(d,a,b,c,x[k+13],S12,0xFD987193);
      c=FF(c,d,a,b,x[k+14],S13,0xA679438E);
      b=FF(b,c,d,a,x[k+15],S14,0x49B40821);
      a=GG(a,b,c,d,x[k+1], S21,0xF61E2562);
      d=GG(d,a,b,c,x[k+6], S22,0xC040B340);
      c=GG(c,d,a,b,x[k+11],S23,0x265E5A51);
      b=GG(b,c,d,a,x[k+0], S24,0xE9B6C7AA);
      a=GG(a,b,c,d,x[k+5], S21,0xD62F105D);
      d=GG(d,a,b,c,x[k+10],S22,0x2441453);
      c=GG(c,d,a,b,x[k+15],S23,0xD8A1E681);
      b=GG(b,c,d,a,x[k+4], S24,0xE7D3FBC8);
      a=GG(a,b,c,d,x[k+9], S21,0x21E1CDE6);
      d=GG(d,a,b,c,x[k+14],S22,0xC33707D6);
      c=GG(c,d,a,b,x[k+3], S23,0xF4D50D87);
      b=GG(b,c,d,a,x[k+8], S24,0x455A14ED);
      a=GG(a,b,c,d,x[k+13],S21,0xA9E3E905);
      d=GG(d,a,b,c,x[k+2], S22,0xFCEFA3F8);
      c=GG(c,d,a,b,x[k+7], S23,0x676F02D9);
      b=GG(b,c,d,a,x[k+12],S24,0x8D2A4C8A);
      a=HH(a,b,c,d,x[k+5], S31,0xFFFA3942);
      d=HH(d,a,b,c,x[k+8], S32,0x8771F681);
      c=HH(c,d,a,b,x[k+11],S33,0x6D9D6122);
      b=HH(b,c,d,a,x[k+14],S34,0xFDE5380C);
      a=HH(a,b,c,d,x[k+1], S31,0xA4BEEA44);
      d=HH(d,a,b,c,x[k+4], S32,0x4BDECFA9);
      c=HH(c,d,a,b,x[k+7], S33,0xF6BB4B60);
      b=HH(b,c,d,a,x[k+10],S34,0xBEBFBC70);
      a=HH(a,b,c,d,x[k+13],S31,0x289B7EC6);
      d=HH(d,a,b,c,x[k+0], S32,0xEAA127FA);
      c=HH(c,d,a,b,x[k+3], S33,0xD4EF3085);
      b=HH(b,c,d,a,x[k+6], S34,0x4881D05);
      a=HH(a,b,c,d,x[k+9], S31,0xD9D4D039);
      d=HH(d,a,b,c,x[k+12],S32,0xE6DB99E5);
      c=HH(c,d,a,b,x[k+15],S33,0x1FA27CF8);
      b=HH(b,c,d,a,x[k+2], S34,0xC4AC5665);
      a=II(a,b,c,d,x[k+0], S41,0xF4292244);
      d=II(d,a,b,c,x[k+7], S42,0x432AFF97);
      c=II(c,d,a,b,x[k+14],S43,0xAB9423A7);
      b=II(b,c,d,a,x[k+5], S44,0xFC93A039);
      a=II(a,b,c,d,x[k+12],S41,0x655B59C3);
      d=II(d,a,b,c,x[k+3], S42,0x8F0CCC92);
      c=II(c,d,a,b,x[k+10],S43,0xFFEFF47D);
      b=II(b,c,d,a,x[k+1], S44,0x85845DD1);
      a=II(a,b,c,d,x[k+8], S41,0x6FA87E4F);
      d=II(d,a,b,c,x[k+15],S42,0xFE2CE6E0);
      c=II(c,d,a,b,x[k+6], S43,0xA3014314);
      b=II(b,c,d,a,x[k+13],S44,0x4E0811A1);
      a=II(a,b,c,d,x[k+4], S41,0xF7537E82);
      d=II(d,a,b,c,x[k+11],S42,0xBD3AF235);
      c=II(c,d,a,b,x[k+2], S43,0x2AD7D2BB);
      b=II(b,c,d,a,x[k+9], S44,0xEB86D391);
      a=AddUnsigned(a,AA);
      b=AddUnsigned(b,BB);
      c=AddUnsigned(c,CC);
      d=AddUnsigned(d,DD);
    }

    var temp = WordToHex(a)+WordToHex(b)+WordToHex(c)+WordToHex(d);

    return temp.toLowerCase();
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
    if (this[0].className === 'alerts-container') {
      var len = $(this).children().length;
      if (len > 2) {
        var children = $(this).children();
        for (var i = 0; i < len - 2; i++) {
          $(children[i]).find('.close').click();
        }
      }
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
  window.authenticated = true;

  var init = function() {
    window.events = new EventCollection();
    window.events.start();

    var headerView = new HeaderView();
    $('body').prepend(headerView.render().el);

    mainRouter.initialize();
  };

  var model = new StateModel();
  model.fetch({
    success: function(model) {
      window.subActive = model.get('active');
      window.subPlan = model.get('plan');
      window.subVer = model.get('version');
      window.subId = '';
      window.theme = model.get('theme');
      window.superUser = model.get('super_user');
      window.sso = model.get('sso');
      window.csrfToken = model.get('csrf_token');

      if (model.get('user')) {
        window.subId = model.get('user').slice(0, 8);
      }

      if (window.subActive && window.theme === 'dark') {
        $('body').addClass('dark');
      }
      else {
        $('body').removeClass('dark');
      }

      if (window.subActive) {
        if (window.subPlan === 'premium') {
          $('body').addClass('premium-' + window.subId);
        }
        else if (window.subPlan === 'enterprise') {
          $('body').addClass('enterprise-' + window.subId);
        }
        else if (window.subPlan === 'enterprise_plus') {
          $('body').addClass('enterprise-plus-' + window.subId);
        }
      }
      else {
        if (window.subPlan === 'premium') {
          $('body').addClass('premium-license');
        }
        else if (window.subPlan === 'enterprise') {
          $('body').addClass('enterprise-license');
        }
        else if (window.subPlan === 'enterprise-plus') {
          $('body').addClass('enterprise-plus-license');
        }
      }

      if (window.superUser) {
        $('body').addClass('super-user');
      } else {
        $('body').removeClass('super-user');
      }

      init();
    },
    error: function() {
      init();
    }
  });
});
