-- PL/pgSQL functions — Users / Auth
-- Requires: schema.sql chạy trước

CREATE OR REPLACE FUNCTION sp_get_user_by_email_or_phone(p_value VARCHAR)
RETURNS TABLE(id INT, full_name VARCHAR, email VARCHAR, phone VARCHAR,
              password VARCHAR, address TEXT, role VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.full_name, u.email, u.phone, u.password, u.address, u.role
    FROM users u
    WHERE u.email = p_value OR u.phone = p_value
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_check_user_exists(p_email VARCHAR, p_phone VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM users WHERE email = p_email OR phone = p_phone);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_register_user(
    p_full_name VARCHAR, p_email VARCHAR, p_phone VARCHAR,
    p_password_hash VARCHAR, p_address TEXT
)
RETURNS INT AS $$
DECLARE new_id INT;
BEGIN
    INSERT INTO users(full_name, email, phone, password, address, role)
    VALUES (p_full_name, p_email, p_phone, p_password_hash, p_address, 'USER')
    RETURNING id INTO new_id;
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_get_user_by_id(p_id INT)
RETURNS TABLE(id INT, full_name VARCHAR, email VARCHAR, phone VARCHAR,
              address TEXT, role VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.full_name, u.email, u.phone, u.address, u.role
    FROM users u WHERE u.id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_update_profile(p_id INT, p_full_name VARCHAR, p_phone VARCHAR, p_address TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET full_name = p_full_name, phone = p_phone, address = p_address
    WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_search_users_paged(
    p_keyword VARCHAR, p_page INT, p_size INT
)
RETURNS TABLE(id INT, full_name VARCHAR, email VARCHAR, phone VARCHAR,
              address TEXT, role VARCHAR, total_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.full_name, u.email, u.phone, u.address, u.role,
           COUNT(*) OVER() AS total_count
    FROM users u
    WHERE p_keyword IS NULL
       OR u.full_name ILIKE '%' || p_keyword || '%'
       OR u.email ILIKE '%' || p_keyword || '%'
       OR u.phone ILIKE '%' || p_keyword || '%'
    ORDER BY u.id
    LIMIT p_size OFFSET (p_page * p_size);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_update_user_role(p_id INT, p_role VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET role = p_role WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_delete_user(p_id INT)
RETURNS VOID AS $$
BEGIN
    DELETE FROM cart_items WHERE user_id = p_id;
    DELETE FROM users WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
