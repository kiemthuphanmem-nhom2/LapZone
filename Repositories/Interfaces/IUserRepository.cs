using LapZoneApi.Models.Dtos;
using LapZoneApi.Models.Entities;

namespace LapZoneApi.Repositories.Interfaces;

public interface IUserRepository
{
    Task<User?> GetByEmailOrPhoneAsync(string value);
    Task<bool> ExistsAsync(string email, string phone);
    Task<int> RegisterAsync(RegisterDto dto, string passwordHash);
    Task<User?> GetByIdAsync(int id);
    Task UpdateProfileAsync(int id, string fullName, string? phone, string? address);
    Task<(IEnumerable<User> Items, int Total)> SearchPagedAsync(string? keyword, int page, int size);
    Task UpdateRoleAsync(int userId, string role);
    Task DeleteAsync(int userId);
}
