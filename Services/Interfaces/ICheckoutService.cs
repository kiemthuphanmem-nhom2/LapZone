using LapZoneApi.Models.Dtos;

namespace LapZoneApi.Services.Interfaces;

public interface ICheckoutService
{
    Task<(int OrderId, decimal Total, string PaymentMethod)> ProcessAsync(
        CheckoutDto dto, int? userId);
}
