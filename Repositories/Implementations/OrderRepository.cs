using Dapper;
using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using Npgsql;

namespace LapZoneApi.Repositories.Implementations;

public class OrderRepository : IOrderRepository
{
    private readonly string _connStr;
    public OrderRepository(IConfiguration config) =>
        _connStr = config.GetConnectionString("DefaultConnection")!;

    private NpgsqlConnection Conn() => new NpgsqlConnection(_connStr);

    public async Task<int> CreateOrderAsync(int? userId, string customerName, string customerPhone,
        string address, string paymentMethod, decimal total)
    {
        using var conn = Conn();
        return await conn.ExecuteScalarAsync<int>(
            "SELECT sp_create_order(@UserId, @CustomerName, @CustomerPhone, @Address, @PaymentMethod, @Total)",
            new { UserId = userId, CustomerName = customerName, CustomerPhone = customerPhone,
                  Address = address, PaymentMethod = paymentMethod, Total = total });
    }

    public async Task InsertOrderDetailAsync(int orderId, int productId, int quantity, decimal price)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_insert_order_detail(@OrderId, @ProductId, @Quantity, @Price)",
            new { OrderId = orderId, ProductId = productId, Quantity = quantity, Price = price });
    }

    public async Task<Order?> GetByIdAsync(int id)
    {
        using var conn = Conn();
        return await conn.QueryFirstOrDefaultAsync<Order>(
            "SELECT * FROM sp_get_order_by_id(@Id)", new { Id = id });
    }

    public async Task<IEnumerable<OrderDetail>> GetDetailsAsync(int orderId)
    {
        using var conn = Conn();
        return await conn.QueryAsync<OrderDetail>(
            "SELECT * FROM sp_get_order_details(@OrderId)", new { OrderId = orderId });
    }

    public async Task DeleteCartItemsAsync(int[] ids)
    {
        using var conn = Conn();
        await conn.ExecuteAsync("SELECT sp_delete_cart_items(@Ids)", new { Ids = ids });
    }

    public async Task<(IEnumerable<Order> Items, int Total)> SearchPagedAsync(
        string? keyword, string? status, DateTime? startDate, DateTime? endDate, int page, int size)
    {
        using var conn = Conn();
        var rows = (await conn.QueryAsync<dynamic>(
            "SELECT * FROM sp_search_orders_paged(@Keyword,@Status,@StartDate,@EndDate,@Page,@Size)",
            new { Keyword = keyword, Status = status, StartDate = startDate,
                  EndDate = endDate, Page = page, Size = size })).ToList();

        var total = rows.Count > 0 ? (int)rows[0].total_count : 0;
        var items = rows.Select(r => new Order
        {
            Id = (int)r.id, TotalAmount = (decimal)r.total_amount, Status = (string)r.status,
            OrderDate = (DateTime)r.order_date, CustomerName = (string)r.customer_name,
            CustomerPhone = (string)r.customer_phone
        });
        return (items, total);
    }

    public async Task UpdateStatusAsync(int orderId, string newStatus)
    {
        using var conn = Conn();
        await conn.ExecuteAsync(
            "SELECT sp_update_order_status(@Id, @Status)", new { Id = orderId, Status = newStatus });
    }
}
