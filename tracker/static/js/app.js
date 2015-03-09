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

  factory.createPackage = function(newPackage) {
    return $http.post('/api/packages', newPackage);
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
      $scope.packages = data.packages;
      console.log(data);
    });
});

packages.controller('PackageController', function($scope, $routeParams, $timeout, Packages) {
  $scope.packageId = $routeParams.packageId;

  $scope.nonEmpty = function(patches) {
    return !jQuery.isEmptyObject(patches)
  }

  Packages.getPackage($scope.packageId)
    .success(function(data, status) {
      $scope.package = data.package;
      var timeout = "";
      if($scope.package.queue_status == "QUEUED") {
        // poll until status changes
        var poller = function() {
          Packages.getPackage($scope.packageId)
          .success(function(data, status) {
            if(data.package.queue_status == "DONE") {
              $timeout.cancel(timeout);
              $scope.package = data.package;
            }
            else if(data.package.queue_status.indexOf("ERROR") > -1) {
              $timeout.cancel(timeout);
              $scope.package = data.package;
            }
            else {
              timeout = $timeout(poller, 10000);
            }
          });
        };
        poller();
      }
    })
    .error(function(data, status) {
      if(status == 404) {
        $scope.notFound = true;
      }
    });
});

packages.controller('PackageCreateController', function($scope, $location, Packages) {
  $scope.package = {};

  $scope.submit = function() {
    var newPackage = $scope.package;
    Packages.createPackage(newPackage)
      .success(function(data, status) {
        $scope.successMessage = data.data.msg;
        $location.path('/packages/' + data.data.id)
      })
      .error(function(data, status) {
        $scope.errorMessage = data.data.msg;
      });

  }
});
