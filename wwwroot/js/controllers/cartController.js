/* Cart controller */
angular.module('lapzoneApp')
.controller('CartController', ['$scope', '$location', 'CartService', 'AuthService',
    function ($scope, $location, CartService, AuthService) {
        if (!AuthService.isLoggedIn()) { $location.path('/login'); return; }
        $scope.cartItems = []; $scope.total = 0; $scope.cartError = null;

        function loadCart() {
            $scope.cartError = null;
            CartService.getCart().then(function (res) {
                var items = (res.data && res.data.items) ? res.data.items : [];
                $scope.cartItems = items.map(function (i) {
                    i.selected = true; return i;
                });
                $scope.total = (res.data && res.data.total) ? res.data.total : 0;
            }, function (err) {
                // 401 sẽ bị interceptor xử lý redirect, các lỗi khác hiển thị thông báo
                if (err.status !== 401) {
                    $scope.cartError = 'Không thể tải giỏ hàng. Vui lòng thử lại.';
                }
            });
        }
        loadCart();

        $scope.updateQuantity = function (item) {
            CartService.update(item.id, item.quantity).then(loadCart);
        };

        $scope.removeItem = function (id) {
            if (!confirm('Xóa sản phẩm này khỏi giỏ hàng?')) return;
            CartService.remove(id).then(loadCart);
        };

        $scope.toggleSelectAll = function () {
            for (var i = 0; i < $scope.cartItems.length; i++) {
                $scope.cartItems[i].selected = $scope.selectAll;
            }
        };

        $scope.calculateTotal = function () {
            var sum = 0;
            if (!$scope.cartItems) return sum;
            for (var i = 0; i < $scope.cartItems.length; i++) {
                var item = $scope.cartItems[i];
                if (item.selected) {
                    sum += item.price * item.quantity;
                }
            }
            return sum;
        };

        $scope.goToCheckout = function () {
            var selected = $scope.cartItems.filter(function (i) { return i.selected; });
            if (selected.length === 0) { alert('Vui lòng chọn ít nhất 1 sản phẩm!'); return; }
            var ids = selected.map(function (i) { return i.id; }).join(',');
            $location.path('/checkout').search({ cartItemIds: ids });
        };
    }]);
