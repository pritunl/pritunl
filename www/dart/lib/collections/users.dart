library users_col;

import 'package:pritunl/exceptions.dart';

import 'package:pritunl/collection.dart' as collec;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;
import 'dart:math' as math;

@Injectable()
class Users extends collec.Collection {
  String _search;
  Type model = usr.User;
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

      this.pageTotal = 0;
      this.pages = [];
    }
    else {
      if (this.page != data['page']) {
        throw new IgnoreResponse();
      }
      this.pageTotal = data['page_total'].toInt();
      this._updatePages();

      this.searchCount = null;
      this.searchMore = null;
      this.searchTime = null;
      this.searchLimit = null;
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

    var isCurPage;
    var cur = math.max(1, this.page - 7);

    this.pages.add([0, 'First']);

    for (var i = 0; i < 15; i++) {
      isCurPage = cur == this.page;
      if (cur > this.pageTotal - 1) {
        break;
      }
      this.pages.add([cur, cur + 1]);
      cur += 1;
    }

    pages.add([this.pageTotal, 'Last']);

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
