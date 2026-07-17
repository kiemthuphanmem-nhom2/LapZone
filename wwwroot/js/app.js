angular.module('lapzoneApp', ['ngRoute'])
    .config(['$routeProvider', function ($routeProvider) {
        $routeProvider
            .when('/', { templateUrl: 'views/product-list.html', controller: 'ProductListController' })
            .when('/products/:id', { templateUrl: 'views/product-detail.html', controller: 'ProductDetailController' })
            .when('/cart', { templateUrl: 'views/cart.html', controller: 'CartController' })
            .when('/checkout', { templateUrl: 'views/checkout.html', controller: 'CheckoutController' })
            .when('/login', { templateUrl: 'views/login.html', controller: 'AuthController' })
            .when('/register', { templateUrl: 'views/register.html', controller: 'RegisterController' })
            .when('/profile', { templateUrl: 'views/profile.html', controller: 'UserController' })
            .when('/orders/lookup', { templateUrl: 'views/order-lookup.html', controller: 'OrderLookupController' })
            .when('/orders/:id', { templateUrl: 'views/order-detail.html', controller: 'OrderDetailController' })
            .when('/admin/categories', { templateUrl: 'views/admin/categories.html', controller: 'AdminCategoryController' })
            .when('/admin/products', { templateUrl: 'views/admin/products.html', controller: 'AdminProductController' })
            .when('/admin/orders', { templateUrl: 'views/admin/orders.html', controller: 'AdminOrderController' })
            .when('/admin/users', { templateUrl: 'views/admin/users.html', controller: 'AdminUserController' })
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
                $location.path('/login');
            };

            $rootScope.$on('$routeChangeSuccess', function () {
                $rootScope.isLoggedIn = AuthService.isLoggedIn();
                $rootScope.isAdmin = AuthService.isAdmin();
                $rootScope.currentUserName = $window.localStorage.getItem('full_name') || '';
                $rootScope.updateCartCount();
            });

            $rootScope.updateCartCount();
        }]);
