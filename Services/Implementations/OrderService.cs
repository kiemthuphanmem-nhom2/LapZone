using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using LapZoneApi.Services.Interfaces;

namespace LapZoneApi.Services.Implementations;

public class OrderService : IOrderService
{
    private readonly IOrderRepository _repo;
    public OrderService(IOrderRepository repo) => _repo = repo;

    public async Task<int> LookupAsync(int orderId, string customerPhone)
    {
        var order = await _repo.GetByIdAsync(orderId);
        if (order == null || order.CustomerPhone != customerPhone.Trim())
            throw new KeyNotFoundException("Không tìm thấy đơn hàng hoặc SĐT không khớp.");
        return order.Id;
    }

    public async Task<Order?> GetDetailAsync(int id)
    {
        var order = await _repo.GetByIdAsync(id);
        if (order == null) return null;
        order.Details = (await _repo.GetDetailsAsync(id)).ToList();
        return order;
    }

    public Task<(IEnumerable<Order> Items, int Total)> SearchPagedAsync(
        string? keyword, string? status, DateTime? startDate, DateTime? endDate, int page, int size)
        => _repo.SearchPagedAsync(keyword, status, startDate, endDate, page, size);

    public Task UpdateStatusAsync(int orderId, string newStatus)
        => _repo.UpdateStatusAsync(orderId, newStatus);
}
