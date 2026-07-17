using LapZoneApi.Models.Entities;

namespace LapZoneApi.Services.Interfaces;

public interface IOrderService
{
    Task<int> LookupAsync(int orderId, string customerPhone);
    Task<Order?> GetDetailAsync(int id);
    Task<(IEnumerable<Order> Items, int Total)> SearchPagedAsync(
        string? keyword, string? status, DateTime? startDate, DateTime? endDate, int page, int size);
    Task UpdateStatusAsync(int orderId, string newStatus);
}
