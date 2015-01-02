library status;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
    selector: 'status',
    templateUrl: 'packages/pritunl/components/status/status.html',
    cssUrl: 'packages/pritunl/components/status/status.css'
)
class StatusComp {
  var recipes;
  var selected;

  StatusComp() {
    this.recipes = this._load();
  }

  select(recipe) {
    this.selected = recipe;
  }

  _load() {
    return [
      new Recipe(
          'My Appetizer 3',
          'Appetizers',
          ['Ingredient 1', 'Ingredient 2'],
          'Some Directions',
          1
      ),
      new Recipe(
          'My Salad',
          'Salads',
          ['Ingredient 1', 'Ingredient 2'],
          'Some Directions',
          3),
      new Recipe(
          'My Soup',
          'Soups',
          ['Ingredient 1', 'Ingredient 2'],
          'Some Directions',
          4),
      new Recipe(
          'My Main Dish',
          'Main Dishes',
          ['Ingredient 1', 'Ingredient 2'],
          'Some Directions',
          2),
      new Recipe(
          'My Side Dish',
          'Side Dishes',
          ['Ingredient 1', 'Ingredient 2'],
          'Some Directions',
          3),
      new Recipe(
          'My Awesome Dessert',
          'Desserts',
          ['Ingredient 1', 'Ingredient 2'],
          'Some Directions',
          5),
      new Recipe(
          'My So-So Dessert',
          'Desserts',
          ['Ingredient 1', 'Ingredient 2'],
          'Some Directions',
          3),
    ];
  }
}

class Recipe {
  var name;
  var category;
  var ingredients;
  var directions;
  var rating;

  Recipe(
    this.name,
    this.category,
    this.ingredients,
    this.directions,
    this.rating
  );
}
