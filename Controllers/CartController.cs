using System.Security.Claims;
using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers;

[ApiController]
[Route("api/cart")]
[Authorize]
public class CartController : ControllerBase
{
    private readonly ICartService _service;
    public CartController(ICartService service) => _service = service;

    private int UserId => int.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);

    [HttpGet]
    public async Task<IActionResult> GetCart()
    {
        var (items, total) = await _service.GetCartAsync(UserId);
        return Ok(new { items, total });
    }

    public class AddCartDto { public int ProductId { get; set; } public int Quantity { get; set; } = 1; }

    [HttpPost("add")]
    public async Task<IActionResult> Add([FromBody] AddCartDto dto)
    {
        await _service.AddAsync(UserId, dto.ProductId, dto.Quantity);
        return Ok(new { success = true });
    }

    public class UpdateCartDto { public int CartItemId { get; set; } public int Quantity { get; set; } }

    [HttpPut("update")]
    public async Task<IActionResult> Update([FromBody] UpdateCartDto dto)
    {
        await _service.UpdateQuantityAsync(dto.CartItemId, dto.Quantity);
        return Ok(new { success = true });
    }

    [HttpDelete("{cartItemId}")]
    public async Task<IActionResult> Remove(int cartItemId)
    {
        await _service.RemoveAsync(cartItemId);
        return Ok(new { success = true });
    }
}
