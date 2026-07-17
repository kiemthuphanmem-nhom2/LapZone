using LapZoneApi.Models.Entities;

namespace LapZoneApi.Repositories.Interfaces;

public interface IOrderRepository
{
    Task<int> CreateOrderAsync(int? userId, string customerName, string customerPhone,
        string address, string paymentMethod, decimal total);
    Task InsertOrderDetailAsync(int orderId, int productId, int quantity, decimal price);
    Task<Order?> GetByIdAsync(int id);
    Task<IEnumerable<OrderDetail>> GetDetailsAsync(int orderId);
    Task DeleteCartItemsAsync(int[] ids);
    Task<(IEnumerable<Order> Items, int Total)> SearchPagedAsync(
        string? keyword, string? status, DateTime? startDate, DateTime? endDate, int page, int size);
    Task UpdateStatusAsync(int orderId, string newStatus);
}
