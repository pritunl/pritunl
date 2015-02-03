library users_col;

import 'package:pritunl/exceptions.dart';

import 'package:pritunl/collection.dart' as collection;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:math' as math;

@Injectable()
class Users extends collection.Collection {
  String _search;
  Type model = user.User;
  String eventType = 'users_updated';
  String org;
  int page;
  int pageTotal;
  List<dynamic> pages;
  int searchCount;
  bool searchMore;
  double searchTime;
  int searchLimit;
  bool noUsers;

  Users(ng.Http http) : super(http);

  String get eventResource {
    return this.org;
  }

  String get url {
    var url = '/user/${this.org}';

    if (this.search != null) {
      url += '?search=${this.search}';
      if (this.searchLimit != null) {
        url += '&limit=${this.searchLimit}';
      }
    }
    else if (this.page != null) {
      url += '?page=${this.page}';
    }

    return url;
  }

  void set search(String val) {
    if (val == '') {
      val = null;
    }

    if (val != this._search) {
      this._search = val;
      this.fetch();
    }
    else {
      this._search = val;
    }
  }
  String get search {
    return this._search;
  }

  List<Map> parse(dynamic data) {
    if (data is! Map) {
      return data;
    }

    if (data.containsKey('search')) {
      if (this._search != data['search']) {
        throw new IgnoreResponse();
      }
      this.searchCount = data['search_count'];
      this.searchMore = data['search_more'];
      this.searchTime = data['search_time'];
      this.searchLimit = data['search_limit'];

      this.pageTotal = null;
    }
    else {
      if (this.page != data['page']) {
        throw new IgnoreResponse();
      }
      this.pageTotal = data['page_total'].toInt();

      this.searchCount = null;
      this.searchMore = null;
      this.searchTime = null;
      this.searchLimit = null;

      this._updatePages();
    }

    return data['users'];
  }

  void imported() {
    for (var user in this) {
      if (user.type == 'client') {
        this.noUsers = false;
        return;
      }
    }
    this.noUsers = true;
  }

  void _updatePages() {
    this.pages = [];

    if (this.pageTotal < 2) {
      return;
    }

    var i;
    var isCurPage;
    var cur = math.max(0, this.page - 7);

    this.pages.add([this.page == 0, 'First']);

    for (i = 0; i < 15; i++) {
      isCurPage = cur == this.page;
      if (cur > this.pageTotal - 1) {
        break;
      }
      if (cur > 0) {
        this.pages.add([isCurPage, cur + 1]);
      }
      cur += 1;
    }

    pages.add([isCurPage, 'Last']);

    this.pages = pages;
  }

  void next() {
    this.page += 1;
    this.fetch();
  }

  void prev() {
    this.page -= 1;
    this.fetch();
  }

  void onPage(dynamic page) {
    if (page == 'First') {
      page = 0;
    }
    else if (page == 'Last') {
      page = this.pageTotal;
    }
    else {
      page -= 1;
    }
    this.page = page;
    this.fetch();
  }

  void searchIncrease() {
    this.searchLimit *= 2;
    this.fetch();
  }
}
