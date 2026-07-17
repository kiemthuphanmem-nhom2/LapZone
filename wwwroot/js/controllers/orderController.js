/* Order controllers */
angular.module('lapzoneApp')

.controller('OrderLookupController', ['$scope', '$location', 'OrderService',
    function ($scope, $location, OrderService) {
        $scope.form = { orderId: '', customerPhone: '' };
        $scope.error = '';

        $scope.lookup = function () {
            $scope.error = '';
            OrderService.lookup($scope.form.orderId, $scope.form.customerPhone)
                .then(function (res) { $location.path('/orders/' + res.data.orderId); },
                      function (err) { $scope.error = (err.data && err.data.message) ? err.data.message : 'Không tìm thấy!'; });
        };
    }])

.controller('OrderDetailController', ['$scope', '$routeParams', 'OrderService',
    function ($scope, $routeParams, OrderService) {
        $scope.order = null;
        OrderService.getDetail($routeParams.id).then(function (res) { $scope.order = res.data; });
    }]);
