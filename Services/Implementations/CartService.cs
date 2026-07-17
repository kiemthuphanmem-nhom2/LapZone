using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using LapZoneApi.Services.Interfaces;

namespace LapZoneApi.Services.Implementations;

public class CartService : ICartService
{
    private readonly ICartRepository _repo;
    public CartService(ICartRepository repo) => _repo = repo;

    public async Task<(IEnumerable<CartItem> Items, decimal Total)> GetCartAsync(int userId)
    {
        var items = await _repo.GetItemsAsync(userId);
        var total = items.Sum(i => i.Price * i.Quantity);
        return (items, total);
    }

    public Task AddAsync(int userId, int productId, int quantity)
        => _repo.AddAsync(userId, productId, quantity);

    public Task UpdateQuantityAsync(int cartItemId, int quantity)
        => _repo.UpdateQuantityAsync(cartItemId, quantity);

    public Task RemoveAsync(int cartItemId) => _repo.RemoveAsync(cartItemId);
}
