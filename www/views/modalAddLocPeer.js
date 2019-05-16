define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkPeer',
  'views/modal',
  'text!templates/modalAddLocPeer.html'
], function($, _, Backbone, LinkPeerModel, ModalView,
    modalAddLocPeerTemplate) {
  'use strict';
  var ModalAddLocPeerView = ModalView.extend({
    className: 'add-location-peer-modal',
    template: _.template(modalAddLocPeerTemplate),
    title: 'Add Location Peer',
    okText: 'Add',
    initialize: function(options) {
      this.link = options.link;
      this.location = options.location;
      this.locations = options.locations;
      ModalAddLocPeerView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template({
        location_id: this.location,
        locations: this.locations.toJSON()
      });
    },
    onOk: function() {
      var peerId = this.$('.peer-id select').val();

      if (!peerId) {
        this.setAlert('danger', 'Missing peer.', '.peer-id');
        return;
      }

      this.setLoading('Adding location peer...');
      var model = new LinkPeerModel();
      model.save({
        link_id: this.link,
        location_id: this.location,
        peer_id: peerId
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    }
  });

  return ModalAddLocPeerView;
});
