using LapZoneApi.Models.Entities;

namespace LapZoneApi.Repositories.Interfaces;

public interface ICartRepository
{
    Task<IEnumerable<CartItem>> GetItemsAsync(int userId);
    Task AddAsync(int userId, int productId, int quantity);
    Task UpdateQuantityAsync(int cartItemId, int quantity);
    Task RemoveAsync(int cartItemId);
}
