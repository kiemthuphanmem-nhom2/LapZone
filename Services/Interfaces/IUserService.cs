using LapZoneApi.Models.Entities;

namespace LapZoneApi.Services.Interfaces;

public interface IUserService
{
    Task<User?> GetByIdAsync(int userId);
    Task UpdateProfileAsync(int userId, string fullName, string? phone, string? address);
    Task<(IEnumerable<User> Items, int Total)> SearchPagedAsync(string? keyword, int page, int size);
    Task UpdateRoleAsync(int userId, string role);
    Task DeleteAsync(int userId);
}
