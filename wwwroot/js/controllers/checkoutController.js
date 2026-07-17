/* Checkout controller */
angular.module('lapzoneApp')
.controller('CheckoutController', ['$scope', '$location', '$routeParams', 'OrderService',
    function ($scope, $location, $routeParams, OrderService) {
        $scope.form = { customerName: '', customerPhone: '', address: '', paymentMethod: 'COD' };
        $scope.loading = false; $scope.error = '';

        var cartItemIds = $location.search().cartItemIds
            ? $location.search().cartItemIds.split(',').map(Number)
            : null;
        var buyNowId = $location.search().buyNowId ? parseInt($location.search().buyNowId) : null;
        var qty = $location.search().qty ? parseInt($location.search().qty) : 1;

        $scope.submit = function () {
            $scope.loading = true; $scope.error = '';
            var dto = {
                customerName: $scope.form.customerName,
                customerPhone: $scope.form.customerPhone,
                address: $scope.form.address,
                paymentMethod: $scope.form.paymentMethod,
                selectedCartItemIds: cartItemIds,
                buyNowProductId: buyNowId,
                buyNowQuantity: qty
            };
            OrderService.process(dto).then(function (res) {
                $location.path('/orders/' + res.data.orderId);
            }, function (err) {
                $scope.error = (err.data && err.data.message) ? err.data.message : 'Có lỗi xảy ra!';
            }).finally(function () { $scope.loading = false; });
        };
    }]);
