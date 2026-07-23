angular.module('lapzoneApp', ['ngRoute'])
    .config(['$routeProvider', function ($routeProvider) {
        var v = '?v=' + Date.now();
        $routeProvider
            .when('/', { templateUrl: 'views/product-list.html' + v, controller: 'ProductListController' })
            .when('/products/:id', { templateUrl: 'views/product-detail.html' + v, controller: 'ProductDetailController' })
            .when('/cart', { templateUrl: 'views/cart.html' + v, controller: 'CartController' })
            .when('/checkout', { templateUrl: 'views/checkout.html' + v, controller: 'CheckoutController' })
            .when('/login', { templateUrl: 'views/login.html' + v, controller: 'AuthController' })
            .when('/register', { templateUrl: 'views/register.html' + v, controller: 'RegisterController' })
            .when('/profile', { templateUrl: 'views/profile.html' + v, controller: 'UserController' })
            .when('/orders/lookup', { templateUrl: 'views/order-lookup.html' + v, controller: 'OrderLookupController' })
            .when('/orders/:id', { templateUrl: 'views/order-detail.html' + v, controller: 'OrderDetailController' })
            .when('/admin/dashboard', { templateUrl: 'views/admin/dashboard.html' + v, controller: 'AdminDashboardController' })
            .when('/admin/categories', { templateUrl: 'views/admin/categories.html' + v, controller: 'AdminCategoryController' })
            .when('/admin/products', { templateUrl: 'views/admin/products.html' + v, controller: 'AdminProductController' })
            .when('/admin/orders', { templateUrl: 'views/admin/orders.html' + v, controller: 'AdminOrderController' })
            .when('/admin/users', { templateUrl: 'views/admin/users.html' + v, controller: 'AdminUserController' })
            .otherwise({ redirectTo: '/' });
    }])
    .config(['$httpProvider', function ($httpProvider) {
        $httpProvider.interceptors.push('authInterceptor');
    }])
    .run(['$rootScope', '$window', '$location', 'AuthService', '$http',
        function ($rootScope, $window, $location, AuthService, $http) {
            $rootScope.isLoggedIn = AuthService.isLoggedIn();
            $rootScope.isAdmin = AuthService.isAdmin();
            $rootScope.currentUserName = $window.localStorage.getItem('full_name') || '';
            $rootScope.cartCount = 0;
            $rootScope.isAdminRoute = $location.path().indexOf('/admin') === 0;
            $rootScope.activePath = $location.path();

            $rootScope.updateCartCount = function () {
                if (AuthService.isLoggedIn()) {
                    $http.get('/api/cart').then(function (res) {
                        var items = (res.data && res.data.items) ? res.data.items : [];
                        var totalQty = 0;
                        for (var i = 0; i < items.length; i++) {
                            totalQty += items[i].quantity;
                        }
                        $rootScope.cartCount = totalQty;
                    }, function () {
                        $rootScope.cartCount = 0;
                    });
                } else {
                    $rootScope.cartCount = 0;
                }
            };

            $rootScope.logout = function () {
                AuthService.logout();
                $rootScope.isLoggedIn = false;
                $rootScope.isAdmin = false;
                $rootScope.currentUserName = '';
                $rootScope.cartCount = 0;
                $rootScope.isAdminRoute = false;
                $rootScope.activePath = '';
                $location.path('/login');
            };

            $rootScope.$on('$routeChangeSuccess', function () {
                $rootScope.isLoggedIn = AuthService.isLoggedIn();
                $rootScope.isAdmin = AuthService.isAdmin();
                $rootScope.currentUserName = $window.localStorage.getItem('full_name') || '';
                $rootScope.isAdminRoute = $location.path().indexOf('/admin') === 0;
                $rootScope.activePath = $location.path();
                $rootScope.updateCartCount();
            });

            $rootScope.updateCartCount();
        }])
    .filter('trustAsHtml', ['$sce', function ($sce) {
        return function (text) {
            return text ? $sce.trustAsHtml(text) : '';
        };
    }]);
