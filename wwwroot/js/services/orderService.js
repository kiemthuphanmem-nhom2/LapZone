angular.module('lapzoneApp').factory('OrderService', ['$http', function ($http) {
    return {
        process: function (dto) { return $http.post('/api/checkout/process', dto); },
        lookup: function (orderId, phone) {
            return $http.post('/api/orders/lookup', { orderId: orderId, customerPhone: phone });
        },
        getDetail: function (id) { return $http.get('/api/orders/' + id); },
        adminSearch: function (params) { return $http.get('/api/admin/orders', { params: params }); },
        updateStatus: function (orderId, newStatus) {
            return $http.put('/api/admin/orders/status', { orderId: orderId, newStatus: newStatus });
        }
    };
}]);
