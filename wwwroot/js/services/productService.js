angular.module('lapzoneApp').factory('ProductService', ['$http', function ($http) {
    return {
        getDetail: function (id) { return $http.get('/api/products/' + id); },
        search: function (params) { return $http.get('/api/products', { params: params }); },
        save: function (dto) { return $http.post('/api/admin/products/save', dto); },
        remove: function (id) { return $http.delete('/api/admin/products/' + id); }
    };
}]);

