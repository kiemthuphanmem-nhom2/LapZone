angular.module('lapzoneApp').factory('CategoryService', ['$http', function ($http) {
    var API = '/api/admin/categories';
    var PUBLIC_API = '/api/categories';
    return {
        getAll: function () { return $http.get(API); },
        getAllPublic: function () { return $http.get(PUBLIC_API); },
        save: function (dto) { return $http.post(API + '/save', dto); },
        remove: function (id) { return $http.delete(API + '/' + id); }
    };
}]);
