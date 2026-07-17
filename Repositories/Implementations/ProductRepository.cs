using Dapper;
using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using Npgsql;

namespace LapZoneApi.Repositories.Implementations;

public class ProductRepository : IProductRepository
{
    private readonly string _connStr;
    public ProductRepository(IConfiguration config) =>
        _connStr = config.GetConnectionString("DefaultConnection")!;

    private NpgsqlConnection Conn() => new NpgsqlConnection(_connStr);

    public async Task<Product?> GetByIdAsync(int id)
    {
        using var conn = Conn();
        return await conn.QueryFirstOrDefaultAsync<Product>(
            "SELECT * FROM sp_get_product_by_id(@Id)", new { Id = id });
    }

    public async Task<IEnumerable<Product>> GetRelatedAsync(int categoryId, int excludeId)
    {
        using var conn = Conn();
        return await conn.QueryAsync<Product>(
            "SELECT * FROM sp_get_related_products(@CategoryId, @ExcludeId)",
            new { CategoryId = categoryId, ExcludeId = excludeId });
    }

    public async Task<(IEnumerable<Product>, int)> SearchAsync(
        string? keyword, int? categoryId, decimal? minPrice, decimal? maxPrice,
        string? cpu, string? gpu, string? ram, string? storage, string? screen,
        string sort, int page, int size)
    {
        using var conn = Conn();
        var rows = (await conn.QueryAsync<dynamic>(
            "SELECT * FROM sp_search_products(@Keyword,@CategoryId,@MinPrice,@MaxPrice,@Cpu,@Gpu,@Ram,@Storage,@Screen,@Sort,@Page,@Size)",
            new { Keyword = keyword, CategoryId = categoryId, MinPrice = minPrice, MaxPrice = maxPrice,
                  Cpu = cpu, Gpu = gpu, Ram = ram, Storage = storage, Screen = screen,
                  Sort = sort, Page = page, Size = size })).ToList();

        var total = rows.Count > 0 ? (int)rows[0].total_count : 0;
        var items = rows.Select(r => new Product
        {
            Id = (int)r.id, Name = (string)r.name, Price = (decimal)r.price,
            Stock = (int)r.stock, Image = (string?)r.image, CategoryId = (int)r.category_id
        });
        return (items, total);
    }

    public async Task<int> InsertAsync(Product p)
    {
        using var conn = Conn();
        return await conn.ExecuteScalarAsync<int>(
            "SELECT sp_insert_product(@Name,@Price,@Stock,@Image,@CategoryId)",
            new { p.Name, p.Price, p.Stock, p.Image, p.CategoryId });
    }

    public async Task UpdateAsync(Product p)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_update_product(@Id,@Name,@Price,@Stock,@Image,@CategoryId)",
            new { p.Id, p.Name, p.Price, p.Stock, p.Image, p.CategoryId });
    }

    public async Task UpsertDetailAsync(int productId, Product d)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(@"SELECT sp_upsert_product_detail(
            @ProductId,@Cpu,@Ram,@Storage,@Gpu,@Screen,@Battery,@Audio,@Ports,@Wireless,
            @Weight,@Color,@ConditionStatus,@Warranty,@MoreInfo)",
            new { ProductId = productId, d.Cpu, d.Ram, d.Storage, d.Gpu, d.Screen, d.Battery,
                  d.Audio, d.Ports, d.Wireless, d.Weight, d.Color, d.ConditionStatus, d.Warranty, d.MoreInfo });
    }

    public async Task DeleteAsync(int id)
    {
        using var conn = Conn();
        await conn.ExecuteAsync("SELECT sp_delete_product(@Id)", new { Id = id });
    }
}
