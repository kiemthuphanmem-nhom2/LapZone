using LapZoneApi.Models.Dtos;
using LapZoneApi.Repositories.Interfaces;
using LapZoneApi.Services.Interfaces;

namespace LapZoneApi.Services.Implementations;

public class CheckoutService : ICheckoutService
{
    private readonly IOrderRepository _orderRepo;
    private readonly IProductRepository _productRepo;
    private readonly ICartRepository _cartRepo;

    public CheckoutService(
        IOrderRepository orderRepo,
        IProductRepository productRepo,
        ICartRepository cartRepo)
    {
        _orderRepo = orderRepo;
        _productRepo = productRepo;
        _cartRepo = cartRepo;
    }

    public async Task<(int OrderId, decimal Total, string PaymentMethod)> ProcessAsync(
        CheckoutDto dto, int? userId)
    {
        List<(int ProductId, int Quantity, decimal Price)> items = new();

        if (dto.SelectedCartItemIds is { Count: > 0 })
        {
            if (userId == null)
                throw new UnauthorizedAccessException("Vui lòng đăng nhập để thanh toán giỏ hàng.");

            var cartItems = await _cartRepo.GetItemsAsync(userId.Value);
            items = cartItems
                .Where(c => dto.SelectedCartItemIds.Contains(c.Id))
                .Select(c => (c.ProductId, c.Quantity, c.Price))
                .ToList();
        }
        else if (dto.BuyNowProductId != null)
        {
            var product = await _productRepo.GetByIdAsync(dto.BuyNowProductId.Value);
            if (product == null)
                throw new ArgumentException("Sản phẩm không tồn tại.");
            items.Add((product.Id, dto.BuyNowQuantity ?? 1, product.Price));
        }
        else
        {
            throw new ArgumentException("Không có sản phẩm để thanh toán.");
        }

        var total = items.Sum(i => i.Price * i.Quantity);
        var orderId = await _orderRepo.CreateOrderAsync(
            userId, dto.CustomerName, dto.CustomerPhone,
            dto.Address, dto.PaymentMethod, total);

        foreach (var item in items)
            await _orderRepo.InsertOrderDetailAsync(orderId, item.ProductId, item.Quantity, item.Price);

        if (dto.SelectedCartItemIds is { Count: > 0 })
            await _orderRepo.DeleteCartItemsAsync(dto.SelectedCartItemIds.ToArray());

        return (orderId, total, dto.PaymentMethod);
    }
}
