/* Product controllers */
angular.module('lapzoneApp')

.controller('ProductListController', ['$scope', '$location', 'ProductService', 'CategoryService',
    function ($scope, $location, ProductService, CategoryService) {
        $scope.products = []; $scope.categories = []; $scope.loading = true;
        $scope.filter = {
            query: $location.search().query || '',
            categoryId: $location.search().categoryId || null,
            sort: $location.search().sort || 'newest',
            page: parseInt($location.search().page) || 0,
            size: 9
        };
        $scope.totalPages = 0; $scope.totalElements = 0;

        CategoryService.getAllPublic().then(function (res) { $scope.categories = res.data; });

        $scope.search = function () {
            $scope.loading = true;
            $scope.filter.page = 0;
            var params = angular.copy($scope.filter);
            ProductService.search(params).then(function (res) {
                $scope.products = res.data.products;
                $scope.totalPages = res.data.totalPages;
                $scope.totalElements = res.data.totalElements;
            }).finally(function () { $scope.loading = false; });
        };

        $scope.goPage = function (p) {
            if (p < 0 || p >= $scope.totalPages) return;
            $scope.filter.page = p;
            $scope.search();
        };

        $scope.search();
    }])

.controller('ProductDetailController', ['$scope', '$routeParams', '$location', 'ProductService', 'CartService', 'AuthService', '$rootScope',
    function ($scope, $routeParams, $location, ProductService, CartService, AuthService, $rootScope) {
        $scope.product = null; $scope.related = []; $scope.qty = 1;

        ProductService.getDetail($routeParams.id).then(function (res) {
            $scope.product = res.data.product;
            $scope.related = res.data.relatedProducts;
        }, function () { $location.path('/'); });

        $scope.addToCart = function () {
            if (!AuthService.isLoggedIn()) { $location.path('/login'); return; }
            var qtyToAdd = $scope.qty;
            CartService.add($scope.product.id, qtyToAdd).then(function () {
                $scope.product.stock -= qtyToAdd;
                $scope.qty = $scope.product.stock > 0 ? 1 : 0;
                if ($rootScope.updateCartCount) $rootScope.updateCartCount();
                alert('Đã thêm vào giỏ hàng!');
            });
        };

        $scope.buyNow = function () {
            $location.path('/checkout').search({ buyNowId: $scope.product.id, qty: $scope.qty });
        };
    }]);
