using System.Security.Claims;
using LapZoneApi.Models.Dtos;
using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers;

[ApiController]
[Route("api/checkout")]
public class CheckoutController : ControllerBase
{
    private readonly ICheckoutService _service;
    public CheckoutController(ICheckoutService service) => _service = service;

    [HttpPost("process")]
    [AllowAnonymous]
    public async Task<IActionResult> Process([FromBody] CheckoutDto dto)
    {
        int? userId = User.Identity?.IsAuthenticated == true
            ? int.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value)
            : null;

        try
        {
            var (orderId, total, paymentMethod) = await _service.ProcessAsync(dto, userId);
            return Ok(new { orderId, total, paymentMethod });
        }
        catch (UnauthorizedAccessException ex) { return Unauthorized(new { message = ex.Message }); }
        catch (ArgumentException ex) { return BadRequest(new { message = ex.Message }); }
        catch (Exception ex) { return BadRequest(new { message = "Có lỗi xảy ra: " + ex.Message }); }
    }
}
