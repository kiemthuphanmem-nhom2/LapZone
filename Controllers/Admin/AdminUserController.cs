using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers.Admin;

[ApiController]
[Route("api/admin/users")]
[Authorize(Policy = "AdminOnly")]
public class AdminUserController : ControllerBase
{
    private readonly IUserService _service;
    public AdminUserController(IUserService service) => _service = service;

    [HttpGet]
    public async Task<IActionResult> Search(
        [FromQuery] string? keyword, [FromQuery] int page = 0, [FromQuery] int size = 20)
    {
        var (items, total) = await _service.SearchPagedAsync(keyword, page, size);
        return Ok(new { users = items, currentPage = page, totalPages = (int)Math.Ceiling(total / (double)size), totalElements = total });
    }

    public class RoleDto { public int UserId { get; set; } public string Role { get; set; } = ""; }

    [HttpPut("role")]
    public async Task<IActionResult> UpdateRole([FromBody] RoleDto dto)
    {
        await _service.UpdateRoleAsync(dto.UserId, dto.Role);
        return Ok(new { success = true });
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        try { await _service.DeleteAsync(id); return Ok(new { success = true }); }
        catch { return BadRequest(new { success = false, message = "Không thể xóa do người này đã có lịch sử mua hàng!" }); }
    }
}
