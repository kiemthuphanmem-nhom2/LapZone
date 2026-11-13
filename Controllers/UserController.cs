using System.Security.Claims;
using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers;

[ApiController]
[Route("api/profile")]
[Authorize]
public class UserController : ControllerBase
{
    private readonly IUserService _service;
    public UserController(IUserService service) => _service = service;
    private int UserId => int.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    [HttpGet]
    public async Task<IActionResult> GetProfile()
    {
        var user = await _service.GetByIdAsync(UserId);
        if (user == null) return NotFound(new { message = "Không tìm thấy người dùng." });
        return Ok(user);
    }

    public class UpdateProfileDto
    {
        public string FullName { get; set; } = "";
        public string? Phone { get; set; }
        public string? Address { get; set; }
    }

    [HttpPut]
    public async Task<IActionResult> UpdateProfile([FromBody] UpdateProfileDto dto)
    {
        await _service.UpdateProfileAsync(UserId, dto.FullName, dto.Phone, dto.Address);
        return Ok(new { success = true });
    }
}
