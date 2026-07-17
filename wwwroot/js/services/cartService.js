angular.module('lapzoneApp').factory('CartService', ['$http', function ($http) {
    var API = '/api/cart';
    return {
        getCart: function () { return $http.get(API); },
        add: function (productId, quantity) {
            return $http.post(API + '/add', { productId: productId, quantity: quantity || 1 });
        },
        update: function (cartItemId, quantity) {
            return $http.put(API + '/update', { cartItemId: cartItemId, quantity: quantity });
        },
        remove: function (cartItemId) { return $http.delete(API + '/' + cartItemId); }
    };
}]);
