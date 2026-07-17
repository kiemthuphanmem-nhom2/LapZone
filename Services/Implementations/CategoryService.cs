using LapZoneApi.Models.Entities;
using LapZoneApi.Repositories.Interfaces;
using LapZoneApi.Services.Interfaces;

namespace LapZoneApi.Services.Implementations;

public class CategoryService : ICategoryService
{
    private readonly ICategoryRepository _repo;
    public CategoryService(ICategoryRepository repo) => _repo = repo;

    public Task<IEnumerable<Category>> GetAllAsync() => _repo.GetAllAsync();
    public Task<Category?> GetByIdAsync(int id) => _repo.GetByIdAsync(id);
    public Task<int> SaveAsync(int? id, string name) => _repo.SaveAsync(id, name);
    public Task DeleteAsync(int id) => _repo.DeleteAsync(id);
}
