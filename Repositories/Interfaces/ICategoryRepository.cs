using LapZoneApi.Models.Entities;

namespace LapZoneApi.Repositories.Interfaces;

public interface ICategoryRepository
{
    Task<IEnumerable<Category>> GetAllAsync();
    Task<Category?> GetByIdAsync(int id);
    Task<int> SaveAsync(int? id, string name);
    Task DeleteAsync(int id);
}
