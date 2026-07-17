/* Admin controllers */
angular.module('lapzoneApp')

/* ── Admin Category ── */
.controller('AdminCategoryController', ['$scope', 'CategoryService',
    function ($scope, CategoryService) {
        $scope.categories = [];
        $scope.form = { id: null, name: '' };

        function load() { CategoryService.getAll().then(function (res) { $scope.categories = res.data; }); }
        load();

        $scope.edit = function (cat) { $scope.form = { id: cat.id, name: cat.name }; };
        $scope.reset = function () { $scope.form = { id: null, name: '' }; };

        $scope.save = function () {
            CategoryService.save($scope.form).then(function () { $scope.reset(); load(); },
                function (err) { alert('Lỗi: ' + ((err.data && err.data.message) ? err.data.message : 'Không xác định')); });
        };

        $scope.remove = function (id) {
            if (!confirm('Xóa danh mục này?')) return;
            CategoryService.remove(id).then(load, function (err) { alert((err.data && err.data.message) ? err.data.message : 'Không thể xóa'); });
        };
    }])

/* ── Admin Product ── */
.controller('AdminProductController', ['$scope', '$http', 'ProductService', 'CategoryService',
    function ($scope, $http, ProductService, CategoryService) {
        $scope.products = []; $scope.categories = [];
        $scope.form = {}; $scope.page = 0; $scope.totalPages = 0;

        CategoryService.getAllPublic().then(function (res) { $scope.categories = res.data; });

        function load() {
            ProductService.search({ page: $scope.page, size: 20 }).then(function (res) {
                $scope.products = res.data.products;
                $scope.totalPages = res.data.totalPages;
            });
        }
        load();

        $scope.newProduct = function () { $scope.form = {}; };
        $scope.edit = function (p) { $scope.form = angular.copy(p); };
        $scope.save = function () {
            ProductService.save($scope.form).then(function () { load(); $scope.form = {}; },
                function (err) { alert('Lỗi: ' + ((err.data && err.data.message) ? err.data.message : 'Không xác định')); });
        };
        $scope.remove = function (id) {
            if (!confirm('Xóa sản phẩm này?')) return;
            ProductService.remove(id).then(load, function (err) { alert((err.data && err.data.message) ? err.data.message : 'Không thể xóa'); });
        };
        $scope.goPage = function (p) { if (p >= 0 && p < $scope.totalPages) { $scope.page = p; load(); } };
    }])

/* ── Admin Order ── */
.controller('AdminOrderController', ['$scope', 'OrderService',
    function ($scope, OrderService) {
        $scope.orders = []; $scope.page = 0; $scope.totalPages = 0;
        $scope.filter = { keyword: '', status: '' };
        var statuses = ['CHỜ XÁC NHẬN', 'CHỜ THANH TOÁN', 'ĐÃ XÁC NHẬN', 'ĐANG GIAO', 'ĐÃ THANH TOÁN', 'HOÀN THÀNH', 'ĐÃ HỦY'];
        $scope.statuses = statuses;

        function load() {
            var params = { page: $scope.page, size: 20 };
            if ($scope.filter.keyword) params.keyword = $scope.filter.keyword;
            if ($scope.filter.status) params.status = $scope.filter.status;
            OrderService.adminSearch(params).then(function (res) {
                $scope.orders = res.data.orders;
                $scope.totalPages = res.data.totalPages;
            });
        }
        load();

        $scope.search = function () { $scope.page = 0; load(); };
        $scope.goPage = function (p) { if (p >= 0 && p < $scope.totalPages) { $scope.page = p; load(); } };
        $scope.updateStatus = function (order) {
            OrderService.updateStatus(order.id, order.status).then(function () {}, function () { load(); });
        };
    }])

/* ── Admin User ── */
.controller('AdminUserController', ['$scope', '$http',
    function ($scope, $http) {
        $scope.users = []; $scope.page = 0; $scope.totalPages = 0;
        $scope.keyword = '';

        function load() {
            var params = { page: $scope.page, size: 20 };
            if ($scope.keyword) params.keyword = $scope.keyword;
            $http.get('/api/admin/users', { params: params }).then(function (res) {
                $scope.users = res.data.users;
                $scope.totalPages = res.data.totalPages;
            });
        }
        load();

        $scope.search = function () { $scope.page = 0; load(); };
        $scope.goPage = function (p) { if (p >= 0 && p < $scope.totalPages) { $scope.page = p; load(); } };

        $scope.updateRole = function (user) {
            $http.put('/api/admin/users/role', { userId: user.id, role: user.role });
        };

        $scope.remove = function (id) {
            if (!confirm('Xóa người dùng này?')) return;
            $http.delete('/api/admin/users/' + id).then(load, function (err) {
                alert((err.data && err.data.message) ? err.data.message : 'Không thể xóa');
            });
        };
    }]);
