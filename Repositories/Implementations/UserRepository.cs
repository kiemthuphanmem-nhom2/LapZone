using Dapper;
using LapZoneApi.Models.Dtos;
using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using Npgsql;

namespace LapZoneApi.Repositories.Implementations;

public class UserRepository : IUserRepository
{
    private readonly string _connStr;
    public UserRepository(IConfiguration config) =>
        _connStr = config.GetConnectionString("DefaultConnection")!;

    private NpgsqlConnection Conn() => new NpgsqlConnection(_connStr);

    public async Task<User?> GetByEmailOrPhoneAsync(string value)
    {
        using var conn = Conn();
        return await conn.QueryFirstOrDefaultAsync<User>(
            "SELECT * FROM sp_get_user_by_email_or_phone(@Value)", new { Value = value });
    }

    public async Task<bool> ExistsAsync(string email, string phone)
    {
        using var conn = Conn();
        return await conn.ExecuteScalarAsync<bool>(
            "SELECT sp_check_user_exists(@Email, @Phone)", new { Email = email, Phone = phone });
    }

    public async Task<int> RegisterAsync(RegisterDto dto, string passwordHash)
    {
        using var conn = Conn();
        return await conn.ExecuteScalarAsync<int>(
            "SELECT sp_register_user(@FullName, @Email, @Phone, @PasswordHash, @Address)",
            new { dto.FullName, dto.Email, dto.Phone, PasswordHash = passwordHash, dto.Address });
    }

    public async Task<User?> GetByIdAsync(int id)
    {
        using var conn = Conn();
        return await conn.QueryFirstOrDefaultAsync<User>(
            "SELECT * FROM sp_get_user_by_id(@Id)", new { Id = id });
    }

    public async Task UpdateProfileAsync(int id, string fullName, string? phone, string? address)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_update_profile(@Id, @FullName, @Phone, @Address)",
            new { Id = id, FullName = fullName, Phone = phone, Address = address });
    }

    public async Task<(IEnumerable<User> Items, int Total)> SearchPagedAsync(
        string? keyword, int page, int size)
    {
        using var conn = Conn();
        var rows = (await conn.QueryAsync<dynamic>(
            "SELECT * FROM sp_search_users_paged(@Keyword, @Page, @Size)",
            new { Keyword = keyword, Page = page, Size = size })).ToList();

        var total = rows.Count > 0 ? (int)rows[0].total_count : 0;
        var items = rows.Select(r => new User
        {
            Id = (int)r.id, FullName = (string)r.full_name, Email = (string)r.email,
            Phone = (string?)r.phone, Address = (string?)r.address, Role = (string)r.role
        });
        return (items, total);
    }

    public async Task UpdateRoleAsync(int userId, string role)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_update_user_role(@Id, @Role)", new { Id = userId, Role = role });
    }

    public async Task DeleteAsync(int userId)
    {
        using var conn = Conn();
        await conn.ExecuteAsync("SELECT sp_delete_user(@Id)", new { Id = userId });
    }
}
