using LapZoneApi.Services.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace LapZoneApi.Controllers;

[ApiController]
[Route("api/products")]
public class ProductController : ControllerBase
{
    private readonly IProductService _service;
    public ProductController(IProductService service) => _service = service;

    // GET /api/products/{id}
    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetDetail(int id)
    {
        var (product, related) = await _service.GetDetailAsync(id);
        if (product == null) return NotFound();
        return Ok(new { product, relatedProducts = related });
    }

    // GET /api/products?query=...&keyword=...&categoryId=...&page=0&size=9
    [HttpGet]
    [HttpGet("/api/search")]
    public async Task<IActionResult> Search(
        [FromQuery] string? query, [FromQuery] string? keyword, [FromQuery] int? categoryId,
        [FromQuery] decimal? minPrice, [FromQuery] decimal? maxPrice,
        [FromQuery] string? cpu, [FromQuery] string? gpu, [FromQuery] string? ram,
        [FromQuery] string? storage, [FromQuery] string? screen,
        [FromQuery] string sort = "newest", [FromQuery] int page = 0, [FromQuery] int size = 12)
    {
        var effectiveKeyword = !string.IsNullOrEmpty(keyword) ? keyword : query;
        var (items, total) = await _service.SearchAsync(effectiveKeyword, categoryId, minPrice, maxPrice,
            cpu, gpu, ram, storage, screen, sort, page, size);
        return Ok(new
        {
            products = items,
            currentPage = page,
            totalPages = (int)Math.Ceiling(total / (double)size),
            totalElements = total
        });
    }
}
