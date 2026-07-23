using Dapper;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Npgsql;

namespace LapZoneApi.Controllers.Admin;

[ApiController]
[Route("api/admin/dashboard")]
[Authorize(Policy = "AdminOnly")]
public class AdminDashboardController : ControllerBase
{
    private readonly string _connStr;
    public AdminDashboardController(IConfiguration config) =>
        _connStr = config.GetConnectionString("DefaultConnection")!;

    [HttpGet("revenue")]
    public async Task<IActionResult> GetMonthlyRevenue()
    {
        using var conn = new NpgsqlConnection(_connStr);
        var revenue = await conn.ExecuteScalarAsync<decimal>("SELECT sp_current_month_revenue()");
        return Ok(new { revenue });
    }

    [HttpGet("stats")]
    public async Task<IActionResult> GetStats()
    {
        using var conn = new NpgsqlConnection(_connStr);
        var productCount = await conn.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM products");
        var categoryCount = await conn.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM categories");
        var orderCount = await conn.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM orders");
        var userCount = await conn.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM users");
        var revenue = await conn.ExecuteScalarAsync<decimal>("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status IN ('ĐÃ THANH TOÁN', 'HOÀN THÀNH')");
        var recentOrders = await conn.QueryAsync("SELECT id, customer_name as customerName, total_amount as totalAmount, status, order_date as orderDate FROM orders ORDER BY id DESC LIMIT 5");

        return Ok(new {
            productCount,
            categoryCount,
            orderCount,
            userCount,
            revenue,
            recentOrders
        });
    }
}
