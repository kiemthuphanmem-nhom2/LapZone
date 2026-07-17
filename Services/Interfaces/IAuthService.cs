using LapZoneApi.Models.Dtos;

namespace LapZoneApi.Services.Interfaces;

public interface IAuthService
{
    Task<int> RegisterAsync(RegisterDto dto);
    Task<AuthResponseDto?> LoginAsync(LoginDto dto);
}
