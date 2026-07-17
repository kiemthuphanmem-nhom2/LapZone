using LapZoneApi.Models.Dtos;
using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;
    public AuthController(IAuthService authService) => _authService = authService;

    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] RegisterDto dto)
    {
        try
        {
            var newId = await _authService.RegisterAsync(dto);
            return Ok(new { message = "Đăng ký thành công!", userId = newId });
        }
        catch (ArgumentException ex) { return BadRequest(new { message = ex.Message }); }
        catch (InvalidOperationException ex) { return BadRequest(new { message = ex.Message }); }
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginDto dto)
    {
        var result = await _authService.LoginAsync(dto);
        if (result == null)
            return Unauthorized(new { message = "Sai tài khoản hoặc mật khẩu!" });
        return Ok(result);
    }
}
