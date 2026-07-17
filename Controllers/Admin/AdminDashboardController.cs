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
}
