/* User profile controller */
angular.module('lapzoneApp')
.controller('UserController', ['$scope', '$http', 'AuthService', '$location',
    function ($scope, $http, AuthService, $location) {
        if (!AuthService.isLoggedIn()) { $location.path('/login'); return; }
        $scope.profile = {}; $scope.success = ''; $scope.error = '';

        $http.get('/api/profile').then(function (res) { $scope.profile = res.data; });

        $scope.save = function () {
            $scope.success = ''; $scope.error = '';
            $http.put('/api/profile', {
                fullName: $scope.profile.fullName || $scope.profile.full_name,
                phone: $scope.profile.phone,
                address: $scope.profile.address
            }).then(function () { $scope.success = 'Cập nhật thành công!'; },
                    function (err) { $scope.error = (err.data && err.data.message) ? err.data.message : 'Có lỗi xảy ra!'; });
        };
    }]);
