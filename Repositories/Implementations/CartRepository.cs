using Dapper;
using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using Npgsql;

namespace LapZoneApi.Repositories.Implementations;

public class CartRepository : ICartRepository
{
    private readonly string _connStr;
    public CartRepository(IConfiguration config) =>
        _connStr = config.GetConnectionString("DefaultConnection")!;

    private NpgsqlConnection Conn() => new NpgsqlConnection(_connStr);

    public async Task<IEnumerable<CartItem>> GetItemsAsync(int userId)
    {
        using var conn = Conn();
        return await conn.QueryAsync<CartItem>(
            "SELECT * FROM sp_get_cart_items(@UserId)", new { UserId = userId });
    }

    public async Task AddAsync(int userId, int productId, int quantity)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_add_to_cart(@UserId, @ProductId, @Quantity)",
            new { UserId = userId, ProductId = productId, Quantity = quantity });
    }

    public async Task UpdateQuantityAsync(int cartItemId, int quantity)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_update_cart_quantity(@CartItemId, @Quantity)",
            new { CartItemId = cartItemId, Quantity = quantity });
    }

    public async Task RemoveAsync(int cartItemId)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_remove_cart_item(@CartItemId)", new { CartItemId = cartItemId });
    }
}
