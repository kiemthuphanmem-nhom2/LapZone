/* Auth controllers */
angular.module('lapzoneApp')

.controller('AuthController', ['$scope', '$location', 'AuthService', '$rootScope',
    function ($scope, $location, AuthService, $rootScope) {
        if (AuthService.isLoggedIn()) { $location.path('/'); return; }
        $scope.credentials = { emailOrPhone: '', password: '' };
        $scope.error = '';
        $scope.loading = false;

        $scope.login = function () {
            $scope.loading = true; $scope.error = '';
            AuthService.login($scope.credentials.emailOrPhone, $scope.credentials.password)
                .then(function (data) {
                    $rootScope.isLoggedIn = true;
                    $rootScope.isAdmin = data.role === 'ADMIN';
                    $rootScope.currentUserName = data.fullName;
                    if ($rootScope.updateCartCount) $rootScope.updateCartCount();
                    $location.path('/');
                }, function (err) {
                    $scope.error = (err.data && err.data.message) ? err.data.message : 'Sai email/SĐT hoặc mật khẩu!';
                }).finally(function () { $scope.loading = false; });
        };
    }])

.controller('RegisterController', ['$scope', '$location', 'AuthService',
    function ($scope, $location, AuthService) {
        $scope.form = { fullName: '', email: '', phone: '', password: '', confirmPassword: '', address: '' };
        $scope.error = ''; $scope.success = '';

        $scope.register = function () {
            $scope.error = ''; $scope.success = '';
            AuthService.register($scope.form).then(function () {
                $scope.success = 'Đăng ký thành công! Đang chuyển hướng đăng nhập...';
                setTimeout(function () { $location.path('/login'); $scope.$apply(); }, 1500);
            }, function (err) {
                $scope.error = err.data.message || 'Đăng ký thất bại!';
            });
        };
    }]);
