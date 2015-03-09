var packages = angular.module('packages', ['ngRoute', 'ui.bootstrap', 'hljs']);

packages.config(function($routeProvider) {
  $routeProvider
    .when('/',
        {
          templateUrl: '/static/partials/index.html'
        })
    .when('/packages/create',
        {
          controller: 'PackageCreateController',
          templateUrl: '/static/partials/package_create.html'
        })
    .when('/packages/:packageId',
        {
          controller: 'PackageController',
          templateUrl: '/static/partials/package.html'
        })
    .when('/packages',
        {
          controller: 'PackagesController',
          templateUrl: '/static/partials/packages.html'
        })
    .otherwise({ redirectTo: '/' });
});

packages.factory('Packages', function($http) {
  var factory = {};

  factory.getPackages = function() {
    return $http.get('/api/packages');
  };

  factory.getPackage = function(id) {
    return $http.get('/api/packages/' + id);
  }

  return factory;
});

packages.controller('PackagesController', function($scope, Packages) {
  $scope.emptyPackages = false;

  Packages.getPackages()
    .success(function(data, status) {
      if(data.packages.length == 0) {
        $scope.emptyPackages = true;
      }
    });
});

packages.controller('PackageController', function($scope, $routeParams, Packages) {
  $scope.packageId = $routeParams.packageId;

  $scope.nonEmpty = function(patches) {
    return !jQuery.isEmptyObject(patches)
  }

  Packages.getPackage($scope.packageId)
    .success(function(data, status) {
      $scope.package = data.package;
      console.log($scope.package);
    })
    .error(function(data, status) {
      if(status == 404) {
        $scope.notFound = true;
      }
    });
});

packages.controller('PackageCreateController', function($scope) {

});
