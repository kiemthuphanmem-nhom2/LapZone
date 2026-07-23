/* Product controllers */
angular.module('lapzoneApp')

.controller('ProductListController', ['$scope', '$location', 'ProductService', 'CategoryService',
    function ($scope, $location, ProductService, CategoryService) {
        $scope.products         = [];
        $scope.filteredProducts = [];
        $scope.categories       = [];
        $scope.loading          = true;
        $scope.brandList        = [];
        $scope.ramList          = [];
        $scope.pageRange        = [];

        $scope.filter = {
            query:      $location.search().query      || '',
            categoryId: $location.search().categoryId || null,
            sort:       $location.search().sort       || 'newest',
            page:       parseInt($location.search().page) || 0,
            size: 9
        };
        $scope.totalPages = 0; $scope.totalElements = 0;

        /* ── Client-side filter state ── */
        $scope.clientFilter = {
            priceMin:    null,
            priceMax:    null,
            brands:      {},
            rams:        {},
            newOnly:     false,
            inStockOnly: false
        };

        CategoryService.getAllPublic().then(function (res) { $scope.categories = res.data; });

        /* ── Build RAM list from loaded products ── */
        function buildRamList(products) {
            var rams = {};
            products.forEach(function (p) { if (p.ram) rams[p.ram] = true; });
            $scope.ramList = Object.keys(rams).sort();
        }

        /* ── Build numbered page range for pagination ── */
        function buildPageRange() {
            var range = [], current = $scope.filter.page, total = $scope.totalPages;
            var start = Math.max(1, current - 2);
            var end   = Math.min(total - 2, current + 2);
            for (var i = start; i <= end; i++) { range.push(i); }
            $scope.pageRange = range;
        }

        /* ── Apply client-side filters (RAM + stock only; brand is server-side via filter.categoryId) ── */
        $scope.applyClientFilter = function () {
            var cf = $scope.clientFilter;
            var minPrice = cf.priceMin ? cf.priceMin * 1000000 : 0;
            var maxPrice = cf.priceMax ? cf.priceMax * 1000000 : Infinity;
            var selectedRams = Object.keys(cf.rams).filter(function (r) { return cf.rams[r]; });

            $scope.filteredProducts = $scope.products.filter(function (p) {
                /* Price */
                if (p.price < minPrice || p.price > maxPrice) return false;
                /* RAM (client-side) */
                if (selectedRams.length && selectedRams.indexOf(p.ram) === -1) return false;
                /* Chỉ hiện còn hàng */
                if (cf.inStockOnly && p.stock <= 0) return false;
                return true;
            });
        };

        /* ── Reset client filters ── */
        $scope.resetClientFilter = function () {
            $scope.clientFilter = { priceMin: null, priceMax: null, rams: {}, inStockOnly: false };
            $scope.filteredProducts = angular.copy($scope.products);
        };

        /* ── Chọn hãng từ sidebar (server-side) ── */
        $scope.selectCategory = function (catId) {
            $scope.filter.categoryId = catId || null;
            $scope.search();
        };

        /* ── Server search ── */
        $scope.search = function () {
            $scope.loading = true;
            $scope.filter.page = 0;
            var params = angular.copy($scope.filter);
            ProductService.search(params).then(function (res) {
                $scope.products         = res.data.products;
                $scope.filteredProducts = angular.copy($scope.products);
                $scope.totalPages       = res.data.totalPages;
                $scope.totalElements    = res.data.totalElements;
                buildRamList($scope.products);
                buildPageRange();
            }).finally(function () { $scope.loading = false; });
        };

        $scope.goPage = function (p) {
            if (p < 0 || p >= $scope.totalPages) return;
            $scope.filter.page = p;
            var params = angular.copy($scope.filter);
            $scope.loading = true;
            ProductService.search(params).then(function (res) {
                $scope.products         = res.data.products;
                $scope.filteredProducts = angular.copy($scope.products);
                $scope.totalPages       = res.data.totalPages;
                $scope.totalElements    = res.data.totalElements;
                buildRamList($scope.products);
                buildPageRange();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }).finally(function () { $scope.loading = false; });
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
