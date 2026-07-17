using LapZoneApi.Models.Entities;

namespace LapZoneApi.Services.Interfaces;

public interface ICartService
{
    Task<(IEnumerable<CartItem> Items, decimal Total)> GetCartAsync(int userId);
    Task AddAsync(int userId, int productId, int quantity);
    Task UpdateQuantityAsync(int cartItemId, int quantity);
    Task RemoveAsync(int cartItemId);
}
