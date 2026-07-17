angular.module('lapzoneApp').factory('AuthService', ['$http', '$window', function ($http, $window) {
    var API = '/api/auth';
    return {
        login: function (emailOrPhone, password) {
            return $http.post(API + '/login', { emailOrPhone: emailOrPhone, password: password })
                .then(function (res) {
                    $window.localStorage.setItem('jwt_token', res.data.token);
                    $window.localStorage.setItem('user_role', res.data.role);
                    $window.localStorage.setItem('full_name', res.data.fullName);
                    $window.localStorage.setItem('user_id', res.data.userId);
                    return res.data;
                });
        },
        register: function (dto) { return $http.post(API + '/register', dto); },
        logout: function () {
            ['jwt_token', 'user_role', 'full_name', 'user_id'].forEach(function (k) {
                $window.localStorage.removeItem(k);
            });
        },
        isLoggedIn: function () { 
            var token = $window.localStorage.getItem('jwt_token');
            return token && token !== 'undefined' && token !== 'null';
        },
        isAdmin: function () { return $window.localStorage.getItem('user_role') === 'ADMIN'; }

    };
}]);
