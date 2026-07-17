using System.Text.Json.Serialization;

namespace LapZoneApi.Models.Entities;

public class User
{
    public int Id { get; set; }
    public string FullName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string? Phone { get; set; }
    [JsonIgnore] // BCrypt hash — KHÔNG bao giờ gửi về client
    public string Password { get; set; } = string.Empty;
    public string? Address { get; set; }
    public string Role { get; set; } = "USER";
}
