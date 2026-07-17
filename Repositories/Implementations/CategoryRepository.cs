using Dapper;
using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using Npgsql;

namespace LapZoneApi.Repositories.Implementations;

public class CategoryRepository : ICategoryRepository
{
    private readonly string _connStr;
    public CategoryRepository(IConfiguration config) =>
        _connStr = config.GetConnectionString("DefaultConnection")!;

    private NpgsqlConnection Conn() => new NpgsqlConnection(_connStr);

    public async Task<IEnumerable<Category>> GetAllAsync()
    {
        using var conn = Conn();
        return await conn.QueryAsync<Category>("SELECT * FROM sp_get_categories()");
    }

    public async Task<Category?> GetByIdAsync(int id)
    {
        using var conn = Conn();
        return await conn.QueryFirstOrDefaultAsync<Category>(
            "SELECT * FROM sp_get_category_by_id(@Id)", new { Id = id });
    }

    public async Task<int> SaveAsync(int? id, string name)
    {
        using var conn = Conn();
        return await conn.ExecuteScalarAsync<int>(
            "SELECT sp_save_category(@Id, @Name)", new { Id = id, Name = name });
    }

    public async Task DeleteAsync(int id)
    {
        using var conn = Conn();
        await conn.ExecuteAsync("SELECT sp_delete_category(@Id)", new { Id = id });
    }
}
