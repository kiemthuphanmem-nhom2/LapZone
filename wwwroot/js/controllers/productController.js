/* Product controllers */
angular.module('lapzoneApp')

.controller('ProductListController', ['$scope', '$location', 'ProductService', 'CategoryService',
    function ($scope, $location, ProductService, CategoryService) {
        $scope.products         = [];
        $scope.filteredProducts = [];
        $scope.categories       = [];
        $scope.loading          = true;
        $scope.brandList        = [];
        $scope.ramList     = ['8 GB', '16 GB', '24 GB', '32 GB', '48 GB'];
        $scope.storageList = ['256 GB', '512 GB', '1 TB'];

        $scope.pageSize      = 9;
        $scope.currentPage   = 0;
        $scope.totalPages    = 0;
        $scope.pagedProducts = [];
        $scope.pageRange     = [];

        $scope.filter = {
            query: $location.search().query || '',
            page:  0,
            size:  100
        };

        /* ── Client-side filter state ── */
        $scope.clientFilter = {
            priceMin:    null,
            priceMax:    null,
            categoryId:  null,
            rams:        {},
            storages:    {},
            conditions:  {},
            inStockOnly: false
        };
        $scope.appliedFilter = {};

        var isRestoring = false;
        /* ── Restore filter state when returning from detail page ── */
        var savedState = ProductService.getFilterState();
        if (savedState) {
            if (savedState.filter) $scope.filter = savedState.filter;
            if (savedState.clientFilter) $scope.clientFilter = savedState.clientFilter;
            if (savedState.appliedFilter) $scope.appliedFilter = savedState.appliedFilter;
            if (savedState.currentPage !== undefined) {
                $scope.currentPage = savedState.currentPage;
                isRestoring = true;
            }
        }

        CategoryService.getAllPublic().then(function (res) { $scope.categories = res.data; });

        /* ── Calculate pagination & slice current page items ── */
        $scope.updatePagination = function () {
            var total = $scope.filteredProducts ? $scope.filteredProducts.length : 0;
            $scope.totalPages = Math.ceil(total / $scope.pageSize);

            if ($scope.currentPage >= $scope.totalPages) {
                $scope.currentPage = Math.max(0, $scope.totalPages - 1);
            }

            var range = [];
            for (var i = 0; i < $scope.totalPages; i++) {
                range.push(i);
            }
            $scope.pageRange = range;

            var start = $scope.currentPage * $scope.pageSize;
            var end   = start + $scope.pageSize;
            $scope.pagedProducts = $scope.filteredProducts.slice(start, end);
        };

        /* ── Change Page ── */
        $scope.goPage = function (p) {
            if (p < 0 || p >= $scope.totalPages) return;
            $scope.currentPage = p;
            $scope.updatePagination();

            ProductService.saveFilterState({
                filter: $scope.filter,
                clientFilter: $scope.clientFilter,
                appliedFilter: $scope.appliedFilter,
                currentPage: $scope.currentPage
            });

            var searchEl = document.getElementById('search-input');
            if (searchEl) {
                searchEl.scrollIntoView({ behavior: 'smooth' });
            } else {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        };

        /* ── Apply client-side filters (Khoảng giá, Hãng sản xuất, RAM, Ổ cứng, Tình trạng) ── */
        $scope.applyClientFilter = function () {
            var cf = $scope.clientFilter;
            var minPrice = cf.priceMin ? cf.priceMin * 1000000 : 0;
            var maxPrice = cf.priceMax ? cf.priceMax * 1000000 : Infinity;
            var selectedRams = Object.keys(cf.rams).filter(function (r) { return cf.rams[r]; });
            var selectedStorages = Object.keys(cf.storages).filter(function (s) { return cf.storages[s]; });
            var selectedConditions = Object.keys(cf.conditions).filter(function (c) { return cf.conditions[c]; });

            var catName = null;
            if (cf.categoryId && $scope.categories) {
                for (var i = 0; i < $scope.categories.length; i++) {
                    if ($scope.categories[i].id == cf.categoryId) {
                        catName = $scope.categories[i].name;
                        break;
                    }
                }
            }

            $scope.appliedFilter = {
                priceMin:     cf.priceMin,
                priceMax:     cf.priceMax,
                categoryId:   cf.categoryId,
                categoryName: catName
            };

            $scope.filteredProducts = $scope.products.filter(function (p) {
                /* Khoảng giá */
                if (p.price < minPrice || p.price > maxPrice) return false;

                /* Hãng sản xuất */
                if (cf.categoryId && p.categoryId != cf.categoryId) return false;

                /* RAM */
                if (selectedRams.length > 0) {
                    if (!p.ram) return false;
                    var ramMatch = selectedRams.some(function (r) {
                        var num = r.replace(/[^0-9]/g, '');
                        var regex = new RegExp('\\b' + num + '\\s*GB\\b', 'i');
                        return regex.test(p.ram);
                    });
                    if (!ramMatch) return false;
                }

                /* Ổ cứng */
                if (selectedStorages.length > 0) {
                    if (!p.storage) return false;
                    var storageMatch = selectedStorages.some(function (s) {
                        var parts = s.split(' ');
                        var num = parts[0];
                        var unit = parts[1] || 'GB';
                        var regex = new RegExp('\\b' + num + '\\s*' + unit + '\\b', 'i');
                        return regex.test(p.storage);
                    });
                    if (!storageMatch) return false;
                }

                /* Tình trạng máy (New / Like New) */
                if (selectedConditions.length > 0) {
                    if (!p.conditionStatus) return false;
                    var condMatch = selectedConditions.some(function (condKey) {
                        var statusUpper = p.conditionStatus.toUpperCase();
                        if (condKey === 'new') {
                            return statusUpper.indexOf('NEW') !== -1 && statusUpper.indexOf('LIKE NEW') === -1;
                        }
                        if (condKey === 'like_new') {
                            return statusUpper.indexOf('LIKE NEW') !== -1;
                        }
                        return false;
                    });
                    if (!condMatch) return false;
                }

                /* Tình trạng kho (Chỉ hiện còn hàng) */
                if (cf.inStockOnly && p.stock <= 0) return false;

                return true;
            });

            if (!isRestoring) {
                $scope.currentPage = 0;
            } else {
                isRestoring = false;
            }
            $scope.updatePagination();

            /* Lưu bộ lọc và trang vào service để khi quay lại từ trang chi tiết sẽ khôi phục */
            ProductService.saveFilterState({
                filter: $scope.filter,
                clientFilter: $scope.clientFilter,
                appliedFilter: $scope.appliedFilter,
                currentPage: $scope.currentPage
            });
        };

        /* ── Reset client filters ── */
        $scope.resetClientFilter = function () {
            $scope.clientFilter = {
                priceMin:    null,
                priceMax:    null,
                categoryId:  null,
                rams:        {},
                storages:    {},
                conditions:  {},
                inStockOnly: false
            };
            $scope.appliedFilter = {};
            $scope.filteredProducts = angular.copy($scope.products);
            $scope.currentPage = 0;
            $scope.updatePagination();
            ProductService.clearFilterState();
        };

        /* ── Server search ── */
        $scope.search = function () {
            $scope.loading = true;
            $scope.filter.page = 0;
            var params = {
                query: $scope.filter.query || '',
                page:  0,
                size:  100
            };
            ProductService.search(params).then(function (res) {
                $scope.products         = res.data.products;
                $scope.filteredProducts = angular.copy($scope.products);
                $scope.totalPages       = res.data.totalPages;
                $scope.totalElements    = res.data.totalElements;
                $scope.applyClientFilter();
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
