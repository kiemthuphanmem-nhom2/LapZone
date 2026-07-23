-- PL/pgSQL functions — Products
-- Requires: schema.sql chạy trước

CREATE OR REPLACE FUNCTION sp_get_product_by_id(p_id INT)
RETURNS TABLE(
    id INT, name VARCHAR, price NUMERIC, stock INT, image VARCHAR,
    category_id INT, category_name VARCHAR,
    cpu VARCHAR, ram VARCHAR, storage VARCHAR, gpu VARCHAR, screen VARCHAR,
    battery VARCHAR, audio VARCHAR, ports VARCHAR, wireless VARCHAR,
    weight VARCHAR, color VARCHAR, condition_status VARCHAR, warranty VARCHAR, more_info TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.name, p.price, p.stock, p.image, p.category_id, c.name,
           pd.cpu, pd.ram, pd.storage, pd.gpu, pd.screen, pd.battery, pd.audio,
           pd.ports, pd.wireless, pd.weight, pd.color, pd.condition_status, pd.warranty, pd.more_info
    FROM products p
    JOIN categories c ON c.id = p.category_id
    LEFT JOIN product_details pd ON pd.product_id = p.id
    WHERE p.id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_get_product_images(p_product_id INT)
RETURNS TABLE(id INT, image_url VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT pi.id, pi.image_url FROM product_images pi WHERE pi.product_id = p_product_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_get_related_products(p_category_id INT, p_exclude_id INT)
RETURNS TABLE(id INT, name VARCHAR, price NUMERIC, image VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.name, p.price, p.image
    FROM products p
    WHERE p.category_id = p_category_id AND p.id <> p_exclude_id
    ORDER BY p.id DESC
    LIMIT 4;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_search_products(
    p_keyword VARCHAR, p_category_id INT, p_min_price NUMERIC, p_max_price NUMERIC,
    p_cpu VARCHAR, p_gpu VARCHAR, p_ram VARCHAR, p_storage VARCHAR, p_screen VARCHAR,
    p_sort VARCHAR, p_page INT, p_size INT
)
RETURNS TABLE(id INT, name VARCHAR, price NUMERIC, stock INT, image VARCHAR,
              category_id INT, cpu VARCHAR, ram VARCHAR, storage VARCHAR, gpu VARCHAR, screen VARCHAR, condition_status VARCHAR,
              total_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.name, p.price, p.stock, p.image, p.category_id,
           pd.cpu, pd.ram, pd.storage, pd.gpu, pd.screen, pd.condition_status,
           COUNT(*) OVER() AS total_count
    FROM products p
    LEFT JOIN product_details pd ON pd.product_id = p.id
    WHERE (p_keyword IS NULL OR p_keyword = '' OR
           p.name ILIKE '%' || p_keyword || '%' OR
           pd.more_info ILIKE '%' || p_keyword || '%')
      AND (p_category_id IS NULL OR p.category_id = p_category_id)
      AND (p_min_price IS NULL OR p.price >= p_min_price)
      AND (p_max_price IS NULL OR p.price <= p_max_price)
      AND (p_cpu IS NULL OR pd.cpu ILIKE '%' || p_cpu || '%')
      AND (p_gpu IS NULL OR pd.gpu ILIKE '%' || p_gpu || '%')
      AND (p_ram IS NULL OR pd.ram ILIKE '%' || p_ram || '%')
      AND (p_storage IS NULL OR pd.storage ILIKE '%' || p_storage || '%')
      AND (p_screen IS NULL OR pd.screen ILIKE '%' || p_screen || '%')
    ORDER BY
      CASE WHEN p_sort = 'price_asc' THEN p.price END ASC,
      CASE WHEN p_sort = 'price_desc' THEN p.price END DESC,
      CASE WHEN p_sort IS NULL OR p_sort = 'newest' THEN p.id END DESC
    LIMIT p_size OFFSET (p_page * p_size);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_insert_product(
    p_name VARCHAR, p_price NUMERIC, p_stock INT, p_image VARCHAR, p_category_id INT
)
RETURNS INT AS $$
DECLARE new_id INT;
BEGIN
    INSERT INTO products(name, price, stock, image, category_id)
    VALUES (p_name, p_price, p_stock, p_image, p_category_id)
    RETURNING id INTO new_id;
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_update_product(
    p_id INT, p_name VARCHAR, p_price NUMERIC, p_stock INT, p_image VARCHAR, p_category_id INT
)
RETURNS VOID AS $$
BEGIN
    UPDATE products SET name = p_name, price = p_price, stock = p_stock,
           image = p_image, category_id = p_category_id
    WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_upsert_product_detail(
    p_product_id INT, p_cpu VARCHAR, p_ram VARCHAR, p_storage VARCHAR, p_gpu VARCHAR,
    p_screen VARCHAR, p_battery VARCHAR, p_audio VARCHAR, p_ports VARCHAR, p_wireless VARCHAR,
    p_weight VARCHAR, p_color VARCHAR, p_condition_status VARCHAR, p_warranty VARCHAR, p_more_info TEXT
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO product_details(product_id, cpu, ram, storage, gpu, screen, battery, audio,
                                 ports, wireless, weight, color, condition_status, warranty, more_info)
    VALUES (p_product_id, p_cpu, p_ram, p_storage, p_gpu, p_screen, p_battery, p_audio,
            p_ports, p_wireless, p_weight, p_color, p_condition_status, p_warranty, p_more_info)
    ON CONFLICT (product_id) DO UPDATE SET
        cpu = EXCLUDED.cpu, ram = EXCLUDED.ram, storage = EXCLUDED.storage, gpu = EXCLUDED.gpu,
        screen = EXCLUDED.screen, battery = EXCLUDED.battery, audio = EXCLUDED.audio,
        ports = EXCLUDED.ports, wireless = EXCLUDED.wireless, weight = EXCLUDED.weight,
        color = EXCLUDED.color, condition_status = EXCLUDED.condition_status,
        warranty = EXCLUDED.warranty, more_info = EXCLUDED.more_info;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_delete_product(p_id INT)
RETURNS VOID AS $$
BEGIN
    DELETE FROM products WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
