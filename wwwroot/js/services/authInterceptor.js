angular.module('lapzoneApp').factory('authInterceptor', ['$window', '$q', function ($window, $q) {
    // Các endpoint không cần JWT — không redirect khi 401
    var AUTH_URLS = ['/api/auth/login', '/api/auth/register'];

    function isAuthUrl(url) {
        for (var i = 0; i < AUTH_URLS.length; i++) {
            if (url && url.indexOf(AUTH_URLS[i]) !== -1) return true;
        }
        return false;
    }

    return {
        request: function (config) {
            var token = $window.localStorage.getItem('jwt_token');
            // Không gắn token khi gọi auth endpoints
            if (token && !isAuthUrl(config.url)) {
                config.headers.Authorization = 'Bearer ' + token;
            }
            return config;
        },
        responseError: function (rejection) {
            if (rejection.status === 401 && !isAuthUrl(rejection.config.url)) {
                // Xóa token cũ nếu hết hạn rồi redirect
                $window.localStorage.removeItem('jwt_token');
                $window.localStorage.removeItem('user_info');
                $window.location.href = '#!/login';
            }
            return $q.reject(rejection);
        }
    };
}]);
