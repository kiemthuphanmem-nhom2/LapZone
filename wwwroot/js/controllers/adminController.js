/* Admin controllers */
angular.module('lapzoneApp')

/* ── Admin Category ── */
.controller('AdminCategoryController', ['$scope', 'CategoryService',
    function ($scope, CategoryService) {

        /* ── State ── */
        $scope.categories = [];
        $scope.form       = { id: null, name: '' };
        $scope.loading    = false;   // Trạng thái đang tải danh sách
        $scope.saving     = false;   // Trạng thái đang lưu (disable nút Save)
        $scope.formError  = '';      // Thông báo lỗi validation trong Modal
        $scope.toast      = { show: false, message: '', type: 'success' };

        /* ── Toast helper ──
         * Dùng Bootstrap Toast API để hiện thông báo nổi góc phải màn hình.
         * type: 'success' | 'danger' | 'warning'
         */
        $scope.showToast = function (msg, type) {
            $scope.toast = { show: true, message: msg, type: type || 'success' };
            var toastEl = document.getElementById('categoryToast');
            if (toastEl) {
                var bsToast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3000 });
                bsToast.show();
            }
        };

        /* ── Load danh sách từ API ── */
        function load() {
            $scope.loading = true;
            CategoryService.getAll()
                .then(function (res) { $scope.categories = res.data; })
                .catch(function () { $scope.showToast('Không thể tải danh sách danh mục!', 'danger'); })
                .finally(function () { $scope.loading = false; });
        }
        load();

        /* ── Reset form và validation về trạng thái ban đầu ── */
        $scope.reset = function () {
            $scope.form      = { id: null, name: '' };
            $scope.formError = '';
        };

        /* ── Mở Modal ở chế độ Thêm mới ── */
        $scope.openAdd = function () {
            $scope.reset();
        };

        /* ── Mở Modal ở chế độ Chỉnh sửa — bind dữ liệu vào $scope.form ── */
        $scope.openEdit = function (cat) {
            $scope.formError = '';
            $scope.form = { id: cat.id, name: cat.name };
        };

        /* ── Lưu (Create hoặc Update) ──
         * Luồng:
         *   1. Validate tên không rỗng
         *   2. Set saving = true (disable nút Save, hiện spinner)
         *   3. Gọi CategoryService.save() → POST /api/admin/categories/save
         *   4. Đóng Modal bằng Bootstrap Modal JS API (không dùng data-bs-dismiss để kiểm soát tốt hơn)
         *   5. Reload danh sách + hiện Toast thành công
         *   6. Nếu lỗi → hiện Toast lỗi (không đóng Modal để user sửa lại)
         */
        $scope.save = function () {
            /* --- Bước 1: Client-side validation --- */
            if (!$scope.form.name || !$scope.form.name.trim()) {
                $scope.formError = 'Tên danh mục không được để trống!';
                return;
            }
            $scope.formError = '';
            $scope.saving = true;

            var isUpdate = !!$scope.form.id;

            /* --- Bước 2: Gọi API --- */
            CategoryService.save($scope.form)
                .then(function () {
                    /* --- Bước 3: Đóng Modal bằng Bootstrap JS API --- */
                    var modalEl = document.getElementById('categoryModal');
                    var bsModal = bootstrap.Modal.getInstance(modalEl);
                    if (bsModal) bsModal.hide();

                    /* --- Bước 4: Reload + Toast --- */
                    load();
                    $scope.showToast(
                        isUpdate ? 'Cập nhật danh mục thành công!' : 'Thêm danh mục mới thành công!',
                        'success'
                    );
                })
                .catch(function (err) {
                    /* Lỗi → hiện Toast, KHÔNG đóng Modal để user có thể sửa */
                    var msg = (err.data && err.data.message) ? err.data.message : 'Đã xảy ra lỗi không xác định';
                    $scope.showToast('Lỗi: ' + msg, 'danger');
                })
                .finally(function () { $scope.saving = false; });
        };

        /* ── Xóa danh mục ── */
        $scope.remove = function (id) {
            /* Confirm dialog trước khi xóa */
            if (!confirm('Bạn có chắc muốn xóa danh mục này?\nThao tác không thể hoàn tác!')) return;

            CategoryService.remove(id)
                .then(function () {
                    load();
                    $scope.showToast('Đã xóa danh mục thành công!', 'success');
                })
                .catch(function (err) {
                    var msg = (err.data && err.data.message) ? err.data.message : 'Không thể xóa danh mục!';
                    $scope.showToast(msg, 'danger');
                });
        };

        /* ── jQuery event: hidden.bs.modal ──
         * Khi Modal đóng HOÀN TOÀN (animation xong), tự động reset form.
         * Dùng $scope.$apply() để AngularJS nhận biết thay đổi từ event jQuery bên ngoài.
         *
         * Lý do dùng jQuery thay vì ng-click trên btn-close:
         *   - Covers TẤT CẢ cách đóng modal: nút X, nút Hủy, click ngoài, phím Esc
         *   - 'hidden.bs.modal' fires SAU animation → tránh flash nội dung form bị reset
         */
        $(document).on('hidden.bs.modal', '#categoryModal', function () {
            $scope.$apply(function () {
                $scope.reset();
            });
        });

        /* ── jQuery event: shown.bs.modal ──
         * Khi Modal mở xong (animation xong), focus vào ô input để user
         * có thể gõ ngay mà không cần click chuột.
         */
        $(document).on('shown.bs.modal', '#categoryModal', function () {
            $('#input-category-name').trigger('focus');
        });

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
    }])

/* ── Admin Dashboard ── */
.controller('AdminDashboardController', ['$scope', '$http',
    function ($scope, $http) {
        $scope.stats = null;
        $scope.loading = true;

        $http.get('/api/admin/dashboard/stats').then(function (res) {
            var stats = res.data;
            if (stats && stats.recentOrders) {
                stats.recentOrders.forEach(function (o) {
                    o.customerName = o.customerName || o.customername || '';
                    o.totalAmount = o.totalAmount || o.totalamount || 0;
                    o.orderDate = o.orderDate || o.orderdate || '';
                });
            }
            $scope.stats = stats;
        }).finally(function () {
            $scope.loading = false;
        });
    }]);
