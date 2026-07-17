using LapZoneApi.Models.Dtos;
using LapZoneApi.Repositories.Interfaces;
using LapZoneApi.Security;
using LapZoneApi.Services.Interfaces;

namespace LapZoneApi.Services.Implementations;

public class AuthService : IAuthService
{
    private readonly IUserRepository _userRepo;
    private readonly JwtTokenService _jwtService;

    public AuthService(IUserRepository userRepo, JwtTokenService jwtService)
    {
        _userRepo = userRepo;
        _jwtService = jwtService;
    }

    public async Task<int> RegisterAsync(RegisterDto dto)
    {
        if (dto.Password != dto.ConfirmPassword)
            throw new ArgumentException("Mật khẩu xác nhận không khớp!");

        var exists = await _userRepo.ExistsAsync(dto.Email, dto.Phone);
        if (exists)
            throw new InvalidOperationException("Email hoặc Số điện thoại đã tồn tại!");

        var hashedPassword = BCrypt.Net.BCrypt.HashPassword(dto.Password);
        return await _userRepo.RegisterAsync(dto, hashedPassword);
    }

    public async Task<AuthResponseDto?> LoginAsync(LoginDto dto)
    {
        var user = await _userRepo.GetByEmailOrPhoneAsync(dto.EmailOrPhone);
        if (user == null || !BCrypt.Net.BCrypt.Verify(dto.Password, user.Password))
            return null;

        var token = _jwtService.GenerateToken(user);
        return new AuthResponseDto
        {
            Token = token,
            FullName = user.FullName,
            Role = user.Role,
            UserId = user.Id
        };
    }
}
