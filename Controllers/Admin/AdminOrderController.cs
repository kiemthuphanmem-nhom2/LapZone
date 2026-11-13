using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers.Admin;

[ApiController]
[Route("api/admin/orders")]
[Authorize(Policy = "AdminOnly")]
public class AdminOrderController : ControllerBase
{
    private readonly IOrderService _service;
    public AdminOrderController(IOrderService service) => _service = service;

    [HttpGet]
    public async Task<IActionResult> Search(
        [FromQuery] string? keyword, [FromQuery] string? status,
        [FromQuery] DateTime? startDate, [FromQuery] DateTime? endDate,
        [FromQuery] int page = 0, [FromQuery] int size = 20)
    {
        if (endDate.HasValue) endDate = endDate.Value.Date.AddHours(23).AddMinutes(59).AddSeconds(59);
        var (items, total) = await _service.SearchPagedAsync(keyword, status, startDate, endDate, page, size);
        return Ok(new { orders = items, currentPage = page, totalPages = (int)Math.Ceiling(total / (double)size), totalElements = total });
    }

    public class StatusDto
    {
        public int OrderId { get; set; }
        public string NewStatus { get; set; } = "";
        public string? Status { get; set; }
    }

    [HttpPut("status")]
    public async Task<IActionResult> UpdateStatus([FromBody] StatusDto dto)
    {
        var targetStatus = !string.IsNullOrEmpty(dto.NewStatus) ? dto.NewStatus : (dto.Status ?? "");
        await _service.UpdateStatusAsync(dto.OrderId, targetStatus);
        return Ok(new { success = true });
    }
}
