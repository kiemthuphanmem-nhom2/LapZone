using LapZoneApi.Models.Entities;
using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers.Admin;

[ApiController]
[Route("api/admin/products")]
[Authorize(Policy = "AdminOnly")]
public class AdminProductController : ControllerBase
{
    private readonly IProductService _service;
    public AdminProductController(IProductService service) => _service = service;

    public class ProductSaveDto
    {
        public int? Id { get; set; }
        public string Name { get; set; } = "";
        public decimal Price { get; set; }
        public int Stock { get; set; }
        public string? Image { get; set; }
        public int CategoryId { get; set; }
        public string? Cpu { get; set; }
        public string? Ram { get; set; }
        public string? Storage { get; set; }
        public string? Gpu { get; set; }
        public string? Screen { get; set; }
        public string? Battery { get; set; }
        public string? Audio { get; set; }
        public string? Ports { get; set; }
        public string? Wireless { get; set; }
        public string? Weight { get; set; }
        public string? Color { get; set; }
        public string? ConditionStatus { get; set; }
        public string? Warranty { get; set; }
        public string? MoreInfo { get; set; }
    }

    [HttpPost("save")]
    public async Task<IActionResult> Save([FromBody] ProductSaveDto dto)
    {
        try
        {
            var product = new Product
            {
                Id = dto.Id ?? 0, Name = dto.Name, Price = dto.Price,
                Stock = dto.Stock, Image = dto.Image, CategoryId = dto.CategoryId,
                Cpu = dto.Cpu, Ram = dto.Ram, Storage = dto.Storage, Gpu = dto.Gpu,
                Screen = dto.Screen, Battery = dto.Battery, Audio = dto.Audio,
                Ports = dto.Ports, Wireless = dto.Wireless, Weight = dto.Weight,
                Color = dto.Color, ConditionStatus = dto.ConditionStatus,
                Warranty = dto.Warranty, MoreInfo = dto.MoreInfo
            };

            if (dto.Id == null)
            {
                var newId = await _service.CreateAsync(product);
                return Ok(new { success = true, id = newId });
            }
            else
            {
                await _service.UpdateAsync(product);
                return Ok(new { success = true, id = dto.Id });
            }
        }
        catch (Exception ex) { return BadRequest(new { success = false, message = ex.Message }); }
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        try { await _service.DeleteAsync(id); return Ok(new { success = true }); }
        catch { return BadRequest(new { success = false, message = "Không thể xóa sản phẩm." }); }
    }
}
