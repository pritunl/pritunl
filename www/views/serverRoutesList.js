define([
  'jquery',
  'underscore',
  'backbone',
  'collections/serverRoute',
  'views/list',
  'views/serverRoutesListItem',
  'text!templates/serverRoutesList.html'
], function($, _, Backbone, ServerRouteCollection, ListView,
    ServerRoutesListItemView, serverRoutesListTemplate) {
  'use strict';
  var ServerRoutesListView = ListView.extend({
    className: 'server-routes-list',
    listContainer: '.routes',
    template: _.template(serverRoutesListTemplate),
    listErrorMsg: 'Failed to load server routes, ' +
      'server error occurred.',
    events: {
      'click .routes-toggle': 'onToggleRoutes',
      'keydown .routes-toggle': 'onToggleKey'
    },
    initialize: function(options) {
      this.collection = new ServerRouteCollection({
        server: options.server.get('id')
      });
      this.listenTo(window.events, 'server_routes_updated:' +
        options.server.get('id'), this.update);
      this.server = options.server;
      this.serverView = options.serverView;
      this.collapsed = this._loadCollapsed();
      ServerRoutesListView.__super__.initialize.call(this);
    },
    render: function() {
      this.$el.html(this.template());
      this._applyCollapsed(false);
      this.$('.routes-toggle').tooltip({
        container: this.el
      });
      this.update();
      return this;
    },
    buildItem: function(model) {
      return new ServerRoutesListItemView({
        model: model,
        server: this.server
      });
    },
    resetItems: function(views) {
      var count = views.length;
      var label;

      label = '(' + count + ')';
      this.$('.routes-toggle-count').text(label);

      if (count) {
        this.$('.routes-toggle').show();
      }
      else {
        this.$('.routes-toggle').hide();
      }
    },
    _showItem: function(view, slide, complete) {
      if (this.collapsed) {
        slide = false;
      }
      ServerRoutesListView.__super__._showItem.call(
        this, view, slide, complete);
    },
    _hideItem: function(view, slide, complete) {
      if (this.collapsed) {
        slide = false;
      }
      ServerRoutesListView.__super__._hideItem.call(
        this, view, slide, complete);
    },
    _storageKey: function() {
      return 'server_routes_collapsed_' + this.server.get('id');
    },
    _loadCollapsed: function() {
      var stored = null;

      try {
        stored = window.localStorage.getItem(this._storageKey());
      }
      catch (err) {
        if (err) {
          return true;
        }
      }

      return stored !== '0';
    },
    _saveCollapsed: function() {
      var value = this.collapsed ? '1' : '0';

      try {
        window.localStorage.setItem(this._storageKey(), value);
      }
      catch (err) {
        if (err) {
          return;
        }
      }
    },
    _setToggleTitle: function(title) {
      var $toggle = this.$('.routes-toggle');
      $toggle.attr('title', title);
      $toggle.attr('data-original-title', title);
    },
    _stopRouteMotion: function() {
      this.$('.routes').children('.route').stop(true, true);
    },
    _clearRouteSizing: function() {
      this.$('.routes').children('.route').css({
        height: '',
        overflow: '',
        marginTop: '',
        marginBottom: '',
        paddingTop: '',
        paddingBottom: ''
      });
    },
    _applyCollapsed: function(animate) {
      var $routes = this.$('.routes');
      var $icon = this.$('.routes-toggle-icon');
      var $toggle = this.$('.routes-toggle');

      this._stopRouteMotion();
      $routes.stop(true, true);

      if (this.collapsed) {
        $icon.removeClass('glyphicon-chevron-down');
        $icon.addClass('glyphicon-chevron-right');
        $toggle.attr('aria-expanded', 'false');
        this._setToggleTitle('Click to expand routes');
        if (animate) {
          $routes.slideUp(window.slideTime);
        }
        else {
          $routes.hide();
        }
      }
      else {
        this._clearRouteSizing();
        $icon.removeClass('glyphicon-chevron-right');
        $icon.addClass('glyphicon-chevron-down');
        $toggle.attr('aria-expanded', 'true');
        this._setToggleTitle('Click to collapse routes');
        if (animate) {
          $routes.slideDown(window.slideTime);
        }
        else {
          $routes.show();
        }
      }
    },
    onToggleKey: function(evt) {
      if (evt.keyCode !== 13 && evt.keyCode !== 32) {
        return;
      }
      evt.preventDefault();
      this.onToggleRoutes();
    },
    onToggleRoutes: function() {
      this.$('.routes-toggle').tooltip('hide');
      this.collapsed = !this.collapsed;
      this._saveCollapsed();
      this._applyCollapsed(true);
    }
  });

  return ServerRoutesListView;
});
