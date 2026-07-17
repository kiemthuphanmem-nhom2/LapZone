using LapZoneApi.Models.Entities;
using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers.Admin;

[ApiController]
[Route("api/admin/categories")]
[Authorize(Policy = "AdminOnly")]
public class AdminCategoryController : ControllerBase
{
    private readonly ICategoryService _service;
    public AdminCategoryController(ICategoryService service) => _service = service;

    [HttpGet]
    public async Task<IActionResult> GetAll() => Ok(await _service.GetAllAsync());

    public class CategorySaveDto { public int? Id { get; set; } public string Name { get; set; } = ""; }

    [HttpPost("save")]
    public async Task<IActionResult> Save([FromBody] CategorySaveDto dto)
    {
        try
        {
            var id = await _service.SaveAsync(dto.Id, dto.Name);
            return Ok(new { success = true, id });
        }
        catch (Exception ex) { return BadRequest(new { success = false, message = ex.Message }); }
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        try
        {
            await _service.DeleteAsync(id);
            return Ok(new { success = true });
        }
        catch { return BadRequest(new { success = false, message = "Không thể xóa! Danh mục đang chứa sản phẩm." }); }
    }
}
