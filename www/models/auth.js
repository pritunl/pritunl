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
      'token': null
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

      if (response.token) {
        tokenData = response.token.split('$');
        hash = new sjcl.hash.sha256();
        hash.update(this.get('username') + '$' + this.get('password'));
        hash.update(sjcl.codec.base64.toBits(tokenData[1]));
        hashDigest = hash.finalize();

        for (i = 0; i < 5; i++) {
          hashDigest = sjcl.hash.sha256.hash(hashDigest);
        }

        cipher = new sjcl.cipher.aes(hashDigest)
        tokenEnc = sjcl.codec.base64.toBits(tokenData[2]);
        response.token = sjcl.codec.utf8String.fromBits(
            cipher.decrypt(tokenEnc.slice(0, 4))) +
          sjcl.codec.utf8String.fromBits(
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
