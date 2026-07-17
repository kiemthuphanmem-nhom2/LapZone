using LapZoneApi.Models.Entities;

namespace LapZoneApi.Repositories.Interfaces;

public interface IProductRepository
{
    Task<Product?> GetByIdAsync(int id);
    Task<IEnumerable<Product>> GetRelatedAsync(int categoryId, int excludeId);
    Task<(IEnumerable<Product> Items, int Total)> SearchAsync(
        string? keyword, int? categoryId, decimal? minPrice, decimal? maxPrice,
        string? cpu, string? gpu, string? ram, string? storage, string? screen,
        string sort, int page, int size);
    Task<int> InsertAsync(Product p);
    Task UpdateAsync(Product p);
    Task UpsertDetailAsync(int productId, Product detail);
    Task DeleteAsync(int id);
}
