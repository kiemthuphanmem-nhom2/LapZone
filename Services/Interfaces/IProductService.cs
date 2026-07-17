using LapZoneApi.Models.Entities;

namespace LapZoneApi.Services.Interfaces;

public interface IProductService
{
    Task<(Product? Product, IEnumerable<Product> Related)> GetDetailAsync(int id);
    Task<(IEnumerable<Product> Items, int Total)> SearchAsync(
        string? keyword, int? categoryId, decimal? minPrice, decimal? maxPrice,
        string? cpu, string? gpu, string? ram, string? storage, string? screen,
        string sort, int page, int size);
    Task<int> CreateAsync(Product product);
    Task UpdateAsync(Product product);
    Task DeleteAsync(int id);
}
