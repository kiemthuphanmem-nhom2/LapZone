namespace LapZoneApi.Models.Entities;

public class Product
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public int Stock { get; set; }
    public string? Image { get; set; }
    public int CategoryId { get; set; }
    public string? CategoryName { get; set; }
    // Chi tiết kỹ thuật (JOIN từ product_details)
    public string? Cpu { get; set; }
    public string? Ram { get; set; }
    public string? Storage { get; set; }
    public string? Gpu { get; set; }
    public string? Screen { get; set; }
    public string? Battery { get; set; }
    public string? Audio { get; set; }
    public string? Ports { get; set; }
    public string? Wireless { get; set; }
    public string? Weight { get; set; }
    public string? Color { get; set; }
    public string? ConditionStatus { get; set; }
    public string? Warranty { get; set; }
    public string? MoreInfo { get; set; }
}
