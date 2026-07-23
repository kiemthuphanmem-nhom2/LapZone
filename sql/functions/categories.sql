-- PL/pgSQL functions — Categories
-- Requires: schema.sql chạy trước

CREATE OR REPLACE FUNCTION sp_get_categories()
RETURNS TABLE(id INT, name VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT c.id, c.name FROM categories c ORDER BY c.id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_get_category_by_id(p_id INT)
RETURNS TABLE(id INT, name VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT c.id, c.name FROM categories c WHERE c.id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_save_category(p_id INT, p_name VARCHAR)
RETURNS INT AS $$
DECLARE result_id INT;
BEGIN
    IF p_id IS NULL THEN
        INSERT INTO categories(name) VALUES (p_name) RETURNING id INTO result_id;
    ELSE
        UPDATE categories SET name = p_name WHERE id = p_id RETURNING id INTO result_id;
    END IF;
    RETURN result_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_delete_category(p_id INT)
RETURNS VOID AS $$
BEGIN
    DELETE FROM categories WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
