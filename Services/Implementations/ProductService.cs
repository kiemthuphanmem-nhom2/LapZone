using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using LapZoneApi.Services.Interfaces;

namespace LapZoneApi.Services.Implementations;

public class ProductService : IProductService
{
    private readonly IProductRepository _repo;
    public ProductService(IProductRepository repo) => _repo = repo;

    public async Task<(Product? Product, IEnumerable<Product> Related)> GetDetailAsync(int id)
    {
        var product = await _repo.GetByIdAsync(id);
        if (product == null) return (null, Enumerable.Empty<Product>());
        var related = await _repo.GetRelatedAsync(product.CategoryId, id);
        return (product, related);
    }

    public Task<(IEnumerable<Product> Items, int Total)> SearchAsync(
        string? keyword, int? categoryId, decimal? minPrice, decimal? maxPrice,
        string? cpu, string? gpu, string? ram, string? storage, string? screen,
        string sort, int page, int size)
        => _repo.SearchAsync(keyword, categoryId, minPrice, maxPrice,
               cpu, gpu, ram, storage, screen, sort, page, size);

    public async Task<int> CreateAsync(Product product)
    {
        var newId = await _repo.InsertAsync(product);
        product.Id = newId;
        await _repo.UpsertDetailAsync(newId, product);
        return newId;
    }

    public async Task UpdateAsync(Product product)
    {
        await _repo.UpdateAsync(product);
        await _repo.UpsertDetailAsync(product.Id, product);
    }

    public Task DeleteAsync(int id) => _repo.DeleteAsync(id);
}
