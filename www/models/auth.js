define([
  'jquery',
  'underscore',
  'backbone',
  'sjcl'
], function($, _, Backbone, SJCL) {
  'use strict';
  var AuthModel = Backbone.Model.extend({
    defaults: {
      'username': null,
      'password': null,
      'token': null,
      'secret': null,
      'email_from': null,
      'email_api_key': null
    },
    url: function() {
      return '/auth';
    },
    parse: function(response) {
      var i;
      var tokenData;
      var hash;
      var hashDigest;
      var cipher;
      var tokenEnc;

      if (response.token && !window.demo) {
        tokenData = response.token.split('$');
        hash = new SJCL.hash.sha256();
        hash.update(this.get('username') + '$' + this.get('password'));
        hash.update(SJCL.codec.base64.toBits(tokenData[1]));
        hashDigest = hash.finalize();

        for (i = 0; i < 5; i++) {
          hashDigest = SJCL.hash.sha256.hash(hashDigest);
        }

        cipher = new SJCL.cipher.aes(hashDigest);
        tokenEnc = SJCL.codec.base64.toBits(tokenData[2]);
        response.token = SJCL.codec.utf8String.fromBits(
            cipher.decrypt(tokenEnc.slice(0, 4))) +
          SJCL.codec.utf8String.fromBits(
            cipher.decrypt(tokenEnc.slice(4, 8)));
      }

      return response;
    },
    isNew: function() {
      return false;
    }
  });

  return AuthModel;
});
