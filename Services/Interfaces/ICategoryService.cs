using LapZoneApi.Models.Entities;

namespace LapZoneApi.Services.Interfaces;

public interface ICategoryService
{
    Task<IEnumerable<Category>> GetAllAsync();
    Task<Category?> GetByIdAsync(int id);
    Task<int> SaveAsync(int? id, string name);
    Task DeleteAsync(int id);
}
