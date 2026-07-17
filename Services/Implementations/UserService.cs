using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using LapZoneApi.Services.Interfaces;

namespace LapZoneApi.Services.Implementations;

public class UserService : IUserService
{
    private readonly IUserRepository _repo;
    public UserService(IUserRepository repo) => _repo = repo;

    public Task<User?> GetByIdAsync(int userId) => _repo.GetByIdAsync(userId);

    public Task UpdateProfileAsync(int userId, string fullName, string? phone, string? address)
        => _repo.UpdateProfileAsync(userId, fullName, phone, address);

    public Task<(IEnumerable<User> Items, int Total)> SearchPagedAsync(string? keyword, int page, int size)
        => _repo.SearchPagedAsync(keyword, page, size);

    public Task UpdateRoleAsync(int userId, string role) => _repo.UpdateRoleAsync(userId, role);

    public Task DeleteAsync(int userId) => _repo.DeleteAsync(userId);
}
