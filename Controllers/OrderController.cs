using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers;

[ApiController]
[Route("api/orders")]
public class OrderController : ControllerBase
{
    private readonly IOrderService _service;
    public OrderController(IOrderService service) => _service = service;

    public class LookupDto { public int OrderId { get; set; } public string CustomerPhone { get; set; } = ""; }

    [HttpPost("lookup")]
    public async Task<IActionResult> Lookup([FromBody] LookupDto dto)
    {
        try
        {
            var orderId = await _service.LookupAsync(dto.OrderId, dto.CustomerPhone);
            return Ok(new { orderId });
        }
        catch (KeyNotFoundException ex) { return NotFound(new { message = ex.Message }); }
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetDetail(int id)
    {
        var order = await _service.GetDetailAsync(id);
        if (order == null) return NotFound();
        return Ok(order);
    }
}
