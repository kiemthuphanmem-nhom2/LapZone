angular.module('lapzoneApp').factory('ProductService', ['$http', function ($http) {
    var savedFilterState = null;

    return {
        getDetail: function (id) { return $http.get('/api/products/' + id); },
        search: function (params) { return $http.get('/api/products', { params: params }); },
        save: function (dto) { return $http.post('/api/admin/products/save', dto); },
        remove: function (id) { return $http.delete('/api/admin/products/' + id); },
        saveFilterState: function (state) {
            savedFilterState = state;
            try { sessionStorage.setItem('lz_filter_state', JSON.stringify(state)); } catch (e) {}
        },
        getFilterState: function () {
            if (savedFilterState) return savedFilterState;
            try {
                var stored = sessionStorage.getItem('lz_filter_state');
                if (stored) {
                    savedFilterState = JSON.parse(stored);
                    return savedFilterState;
                }
            } catch (e) {}
            return null;
        },
        clearFilterState: function () {
            savedFilterState = null;
            try { sessionStorage.removeItem('lz_filter_state'); } catch (e) {}
        }
    };
}]);

