-- =============================================================================
-- LAPZONE API - FILE SQL TỔNG HỢP (SCHEMA + FUNCTIONS + SEED DATA)
-- Chạy 1 file duy nhất này trong pgAdmin Query Tool hoặc psql để tạo/reset toàn bộ DB
-- =============================================================================


-- =========================================================
-- LapZoneApi — Database Schema PostgreSQL
-- Chạy file này trước tất cả các file sql/functions/*.sql
-- =========================================================

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    full_name     VARCHAR(255) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    phone         VARCHAR(20) UNIQUE,
    password      VARCHAR(255) NOT NULL,
    address       TEXT,
    role          VARCHAR(20) NOT NULL DEFAULT 'USER'
);

CREATE TABLE IF NOT EXISTS categories (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    price       NUMERIC(14,2) NOT NULL,
    stock       INT NOT NULL DEFAULT 0,
    image       VARCHAR(500),
    category_id INT NOT NULL REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS product_details (
    id               SERIAL PRIMARY KEY,
    cpu              VARCHAR(255),
    ram              VARCHAR(255),
    storage          VARCHAR(255),
    gpu              VARCHAR(255),
    screen           VARCHAR(255),
    battery          VARCHAR(255),
    audio            VARCHAR(255),
    ports            VARCHAR(255),
    wireless         VARCHAR(255),
    weight           VARCHAR(50),
    color            VARCHAR(100),
    condition_status VARCHAR(100),
    warranty         VARCHAR(100),
    more_info        TEXT,
    product_id       INT NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS product_images (
    id         SERIAL PRIMARY KEY,
    image_url  VARCHAR(500) NOT NULL,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cart_items (
    id         SERIAL PRIMARY KEY,
    quantity   INT NOT NULL DEFAULT 1,
    user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id             SERIAL PRIMARY KEY,
    total_amount   NUMERIC(14,2) NOT NULL,
    status         VARCHAR(50) NOT NULL,
    order_date     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    customer_name  VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    address        TEXT NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    user_id        INT REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_details (
    id         SERIAL PRIMARY KEY,
    quantity   INT NOT NULL,
    price      NUMERIC(14,2) NOT NULL,
    order_id   INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_cart_user ON cart_items(user_id);
CREATE INDEX IF NOT EXISTS idx_orderdetails_order ON order_details(order_id);


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


-- PL/pgSQL functions — Cart
-- Requires: schema.sql chạy trước

CREATE OR REPLACE FUNCTION sp_get_cart_items(p_user_id INT)
RETURNS TABLE(id INT, quantity INT, product_id INT, product_name VARCHAR,
              price NUMERIC, image VARCHAR, stock INT) AS $$
BEGIN
    RETURN QUERY
    SELECT ci.id, ci.quantity, p.id, p.name, p.price, p.image, p.stock
    FROM cart_items ci
    JOIN products p ON p.id = ci.product_id
    WHERE ci.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_add_to_cart(p_user_id INT, p_product_id INT, p_quantity INT)
RETURNS VOID AS $$
DECLARE existing_id INT; existing_qty INT; stock_qty INT;
BEGIN
    SELECT stock INTO stock_qty FROM products WHERE id = p_product_id;
    SELECT id, quantity INTO existing_id, existing_qty
        FROM cart_items WHERE user_id = p_user_id AND product_id = p_product_id;

    IF existing_id IS NOT NULL THEN
        UPDATE cart_items
        SET quantity = LEAST(existing_qty + p_quantity, stock_qty)
        WHERE id = existing_id;
    ELSE
        INSERT INTO cart_items(user_id, product_id, quantity)
        VALUES (p_user_id, p_product_id, LEAST(p_quantity, stock_qty));
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_update_cart_quantity(p_cart_item_id INT, p_quantity INT)
RETURNS VOID AS $$
DECLARE prod_id INT; stock_qty INT;
BEGIN
    IF p_quantity IS NULL OR p_quantity <= 0 THEN
        DELETE FROM cart_items WHERE id = p_cart_item_id;
        RETURN;
    END IF;

    SELECT product_id INTO prod_id FROM cart_items WHERE id = p_cart_item_id;
    SELECT stock INTO stock_qty FROM products WHERE id = prod_id;

    UPDATE cart_items SET quantity = LEAST(p_quantity, stock_qty) WHERE id = p_cart_item_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_remove_cart_item(p_cart_item_id INT)
RETURNS VOID AS $$
BEGIN
    DELETE FROM cart_items WHERE id = p_cart_item_id;
END;
$$ LANGUAGE plpgsql;


-- PL/pgSQL functions — Orders / Checkout
-- Requires: schema.sql chạy trước

CREATE OR REPLACE FUNCTION sp_create_order(
    p_user_id INT, p_customer_name VARCHAR, p_customer_phone VARCHAR,
    p_address TEXT, p_payment_method VARCHAR, p_total_amount NUMERIC
)
RETURNS INT AS $$
DECLARE new_id INT; v_status VARCHAR;
BEGIN
    v_status := CASE WHEN p_payment_method = 'COD' THEN 'CHỜ XÁC NHẬN' ELSE 'CHỜ THANH TOÁN' END;

    INSERT INTO orders(user_id, customer_name, customer_phone, address, payment_method, total_amount, status, order_date)
    VALUES (p_user_id, p_customer_name, p_customer_phone, p_address, p_payment_method, p_total_amount, v_status, CURRENT_TIMESTAMP)
    RETURNING id INTO new_id;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_insert_order_detail(p_order_id INT, p_product_id INT, p_quantity INT, p_price NUMERIC)
RETURNS VOID AS $$
BEGIN
    INSERT INTO order_details(order_id, product_id, quantity, price)
    VALUES (p_order_id, p_product_id, p_quantity, p_price);

    -- Trừ số lượng tồn kho của sản phẩm tương ứng
    UPDATE products 
    SET stock = GREATEST(stock - p_quantity, 0) 
    WHERE id = p_product_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_get_order_by_id(p_id INT)
RETURNS TABLE(id INT, total_amount NUMERIC, status VARCHAR, order_date TIMESTAMP,
              customer_name VARCHAR, customer_phone VARCHAR, address TEXT,
              payment_method VARCHAR, user_id INT) AS $$
BEGIN
    RETURN QUERY SELECT o.id, o.total_amount, o.status, o.order_date, o.customer_name,
                        o.customer_phone, o.address, o.payment_method, o.user_id
                 FROM orders o WHERE o.id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_get_order_details(p_order_id INT)
RETURNS TABLE(id INT, quantity INT, price NUMERIC, product_id INT, product_name VARCHAR, product_image VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT od.id, od.quantity, od.price, p.id, p.name, p.image
    FROM order_details od JOIN products p ON p.id = od.product_id
    WHERE od.order_id = p_order_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_delete_cart_items(p_ids INT[])
RETURNS VOID AS $$
BEGIN
    DELETE FROM cart_items WHERE id = ANY(p_ids);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_search_orders_paged(
    p_keyword VARCHAR, p_status VARCHAR, p_start_date TIMESTAMP, p_end_date TIMESTAMP,
    p_page INT, p_size INT
)
RETURNS TABLE(id INT, total_amount NUMERIC, status VARCHAR, order_date TIMESTAMP,
              customer_name VARCHAR, customer_phone VARCHAR, total_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT o.id, o.total_amount, o.status, o.order_date, o.customer_name, o.customer_phone,
           COUNT(*) OVER() AS total_count
    FROM orders o
    WHERE (p_status IS NULL OR o.status = p_status)
      AND (p_keyword IS NULL OR o.customer_name ILIKE '%'||p_keyword||'%'
                             OR o.customer_phone ILIKE '%'||p_keyword||'%'
                             OR CAST(o.id AS TEXT) ILIKE '%'||p_keyword||'%')
      AND (p_start_date IS NULL OR o.order_date >= p_start_date)
      AND (p_end_date IS NULL OR o.order_date <= p_end_date)
    ORDER BY o.order_date DESC
    LIMIT p_size OFFSET (p_page * p_size);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_update_order_status(p_id INT, p_status VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE orders SET status = p_status WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_current_month_revenue()
RETURNS NUMERIC AS $$
DECLARE result NUMERIC;
BEGIN
    SELECT COALESCE(SUM(total_amount), 0) INTO result
    FROM orders
    WHERE status IN ('ĐÃ THANH TOÁN', 'HOÀN THÀNH')
      AND EXTRACT(MONTH FROM order_date) = EXTRACT(MONTH FROM CURRENT_DATE)
      AND EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE);
    RETURN result;
END;
$$ LANGUAGE plpgsql;


-- =======================================================================
-- SCRIPT SEED DỮ LIỆU MẪU POSTGRESQL CHO LAPZONE
-- Sử dụng sau khi đã chạy sql/schema.sql thành công.
-- Có thể copy dán chạy trực tiếp trong DBeaver.
-- =======================================================================

-- 1. Seed Categories
INSERT INTO categories (id, name) VALUES
(1, 'Acer'),
(2, 'Gigabyte'),
(3, 'Apple'),
(4, 'Asus'),
(5, 'Dell'),
(6, 'HP'),
(7, 'Lenovo')
ON CONFLICT (id) DO NOTHING;

-- Thiết lập lại sequence cho categories
SELECT setval('categories_id_seq', COALESCE((SELECT MAX(id)+1 FROM categories), 1), false);

-- 2. Seed Products (1 -> 22 và 101 -> 118)
INSERT INTO products (id, name, price, stock, image, category_id) VALUES
(1, 'Dell G15 5530 2023 i5-13450HX RAM 16GB SSD 512GB RTX 3050 15.6" FHD 120Hz', 22990000.00, 2, 'assets/Dell_gaming_G15_5530_img0.jpg', 5),
(2, 'Gigabyte Gaming A16 GA6H CMHH2VN893SH i5-13420H RAM 16GB SSD 512GB RTX 4050 16" FHD+ 165Hz', 22990000.00, 3, 'assets/gigabyte_gaming_a16_img0.png', 2),
(3, 'Lenovo IdeaPad Slim 3 15IRH10 2025 i5 13420H RAM 16GB SSD 512GB 15.1" 2.5K OLED 165Hz', 17890000.00, 1, 'assets/ideapad_slim3_15irh10_img0.png', 7),
(4, 'Thinkbook 14 G7+ 2025 Ultra 5 225H RAM 32GB SSD 1TB 14.5" 3K 120Hz', 21590000.00, 2, 'assets/thinkbook_14_g7_img0.jpg', 7),
(5, 'Acer Shadow Knight 6 i7 14650HX RAM 16GB SSD 1TB RTX 4060 16" 2.5K 240Hz', 25990000.00, 1, 'assets/acer_sadow_desc_img0.png', 1),
(6, 'Lenovo IdeaPad 5 Pro 14 GT 2025 Ryzen AI 9 365 RAM 32GB SSD 1TB 14" 2.8K OLED 120Hz', 26190000.00, 1, 'assets/ideapad_5pro_14gt_img0.jpg', 7),
(7, 'Lenovo IdeaPad Slim 5 2025 Ryzen 7 H 255 RAM 24GB SSD 1TB 2.8K OLED 120Hz', 18490000.00, 2, 'assets/ideapad_slim5_2025_img0.png', 7),
(8, 'Lenovo Legion Y7000P 16IRX10 2025 i9 14900HX RAM 16GB SSD 1TB RTX 5060 16" 2.5K 240Hz', 34490000.00, 1, 'assets/y7000_2025_img0.jpg', 7),
(9, 'Lenovo IdeaPad 5 Pro 16 GT 2025 Ultra 5 225H RAM 32GB SSD 1TB 16" 2.8K OLED 120Hz', 23900000.00, 1, 'assets/ideapad_5pro_16gt_img0.jpg', 7),
(10, 'Gigabyte Gaming A16 GA6H CMHH2VN893SH i5-13420H RAM 16GB SSD 512GB RTX 4050 16" FHD+ 165Hz', 22990000.00, 3, 'assets/gigabyte_gaming_a16_img0.png', 2),
(11, 'Lenovo Legion 5 Y7000 15IRX10 2025 i7 14650HX RAM 16GB SSD 512GB RTX 5060 15.3" 2.5K 180Hz', 30900000.00, 2, 'assets/y7000_2025_img0.jpg', 7),
(12, 'Lenovo Legion Pro 5 R9000P 16ADR10 2025 Ryzen 9 8945HX RAM 32GB SSD 1TB RTX 5060 16" 2.5K 240Hz', 34990000.00, 1, 'assets/legion_pro5_r9000p_img0.jpg', 7),
(13, 'Lenovo IdeaPad Slim 3 15IRH10 2025 i5 13420H RAM 16GB SSD 512GB 15.1" 2.5K OLED 165Hz', 17890000.00, 0, 'assets/ideapad_slim3_15irh10_img0.png', 7),
(14, 'Thinkbook 14 G7+ 2025 Ultra 5 225H RAM 32GB SSD 1TB 14.5" 3K 120Hz', 21590000.00, 1, 'assets/thinkbook_14_g7_img0.jpg', 7),
(15, 'Macbook Pro 14 M2 Pro 10 Core RAM 16GB SSD 512GB 16 GPU Liquid Retina', 34700000.00, 2, 'assets/macbook_pro14_M2_img0.jpg', 3),
(16, 'Macbook Pro 16 M1 Pro RAM 16GB SSD 512GB Liquid Retina 2021', 31500000.00, 2, 'assets/macbook_pro_16m1_img0.jpg', 3),
(17, 'Macbook Pro 14 M1 Pro 10-core CPU 16-core GPU RAM 16GB SSD 512GB Retina 2021', 30200000.00, 2, 'assets/macbook_pro_14_m1_img0.png', 3),
(18, 'Macbook Pro 14 M1 Pro 8-Core CPU 14-Core GPU RAM 16GB SSD 512GB Retina 2021 - Bảo Hành 03 tháng', 27500000.00, 2, 'assets/macbook_pro_14_m1_img0.png', 3),
(19, 'Macbook Pro 16 M1 Pro RAM 16GB SSD 512GB Liquid Retina 2021', 31500000.00, 2, 'assets/macbook_pro_16m1_img0.jpg', 3),
(20, 'acer nitroV sieu cap', 25000000.00, 1, 'assets/idea_padpro_14gt.jpg', 1),
(21, 'Dell Precision 5580', 35000000.00, 1, 'assets/dohoakythuat.webp', 5),
(22, 'acer nitroV', 23000000.00, 1, 'assets/acer_sadow_desc_img0.png', 1),
(101, 'Acer Predator Helios Neo 16 (2024)', 32990000.00, 15, 'assets/acer_helios_neo_16_img0.jpg', 1),
(102, 'Acer Nitro V 15 (2024)', 24590000.00, 20, 'assets/acer_nitro_v15_img0.jpg', 1),
(103, 'Acer Swift Go 14 OLED (2024)', 19990000.00, 10, 'assets/acer_swift_go14_img0.jpg', 1),
(104, 'Asus ROG Zephyrus G14 (2024)', 39990000.00, 8, 'assets/asus_rog_g14_img0.jpg', 4),
(105, 'Asus TUF Gaming A15 (2024)', 26490000.00, 12, 'assets/asus_tuf_a15_img0.jpg', 4),
(106, 'Asus Zenbook S 13 OLED (2024)', 29990000.00, 5, 'assets/asus_zenbook_s13_img0.jpg', 4),
(107, 'Dell XPS 15 9530 (2024)', 45990000.00, 5, 'assets/dell_xps_15_img0.jpg', 5),
(108, 'Dell Inspiron 16 Plus 7630 (2024)', 28990000.00, 8, 'assets/dell_inspiron_16_img0.jpg', 5),
(109, 'Dell Alienware m16 R2 (2024)', 52990000.00, 3, 'assets/dell_alienware_m16_img0.jpg', 5),
(110, 'Lenovo Legion Slim 5 16IRH8 (2024)', 29990000.00, 12, 'assets/lenovo_legion_slim5_img0.jpg', 7),
(111, 'Lenovo LOQ 15IRX9 (2024)', 23990000.00, 25, 'assets/lenovo_loq_15_img0.jpg', 7),
(112, 'Lenovo ThinkPad T14 Gen 4 (2024)', 34500000.00, 10, 'assets/lenovo_thinkpad_t14_img0.jpg', 7),
(113, 'HP Omen 16 (2024)', 31500000.00, 7, 'assets/hp_omen_16_img0.jpg', 6),
(114, 'HP Victus 16 (2024)', 22990000.00, 15, 'assets/hp_victus_16_img0.jpg', 6),
(115, 'HP Envy x360 14 (2024)', 25990000.00, 10, 'assets/hp_envy_x360_img0.jpg', 6),
(116, 'MacBook Air 15 inch M3 (2024)', 32990000.00, 20, 'assets/macbook_air_15_m3_img0.jpg', 3),
(117, 'MacBook Air 13 inch M3 (2024)', 27990000.00, 30, 'assets/macbook_air_13_m3_img0.jpg', 3),
(118, 'MacBook Pro 16 inch M3 Max (2024)', 89990000.00, 5, 'assets/macbook_pro_16_m3max_img0.jpg', 3)
ON CONFLICT (id) DO NOTHING;

-- Thiết lập lại sequence cho products
SELECT setval('products_id_seq', COALESCE((SELECT MAX(id)+1 FROM products), 1), false);

-- 3. Seed Product Details
INSERT INTO product_details (product_id, cpu, ram, storage, gpu, screen, battery, audio, ports, wireless, weight, color, condition_status, warranty, more_info) VALUES
(1, 'Intel Core i5 13450HX (10 nhân, 12 luồng, tối đa 4.6GHz)', '16GB DDR5 4800MHz, 2 khe RAM, hỗ trợ nâng cấp', '512GB SSD NVMe, 1 slot, hỗ trợ mở rộng', 'NVIDIA GeForce RTX 3050 6GB GDDR6', '15.6" FHD IPS (1920x1080), 120Hz, 250 nits, 45% NTSC', '56Wh', '2 loa stereo, Dolby Audio', '2 USB-A 3.2 Gen 1, 1 USB-C 3.2 Gen 2, HDMI 2.0, jack 3.5mm', 'Wi-Fi 6, Bluetooth 5.1', '2.5kg', 'Đen', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 13450HX<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 15.6" FHD IPS (1920x1080), 120Hz<br>-Đồ họa: NVIDIA GeForce RTX 3050 6GB'),
(2, 'Intel Core i5 13420H (8 nhân, 12 luồng, tối đa 4.8GHz)', '16GB DDR5 5200MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 1 slot, hỗ trợ mở rộng', 'Nvidia GeForce RTX 4050 6GB GDDR6', '16" FHD+ (1920x1200) IPS, 165Hz, 300 nits, 72% NTSC', '65Wh', '2 loa, DTS:X Ultra', '1 USB-C 3.2 Gen 2, 2 USB-A 3.2 Gen 1, HDMI 2.1, jack 3.5mm', 'Wi-Fi 6E, Bluetooth 5.2', '2.2kg', 'Xám', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 13420H<br>-RAM: 16GB DDR5 5200MHz<br>-Màn hình: 16" FHD+ (1920x1200) IPS, 165Hz<br>-Đồ họa: Nvidia GeForce RTX 4050 6GB'),
(3, 'Intel Core i5 13420H (8 nhân, 12 luồng, tối đa 4.7GHz)', '16GB DDR5 4800MHz, 1 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 1 slot, hỗ trợ mở rộng', 'Intel UHD Graphics', '15.1" 2.5K (2560x1600) OLED, 165Hz, 500 nits, 100% sRGB', '45Wh', '2 loa, Dolby Audio', '1 USB-C 3.2 Gen 2, 2 USB-A 3.0, HDMI 1.4, jack 3.5mm', 'Wi-Fi 5, Bluetooth 5.0', '1.7kg', 'Xám bạc', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 13420H<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 15.1", 2.5K (2560x1600) OLED, 500nits<br>-Đồ họa: Intel UHD Graphics'),
(4, 'Intel Core Ultra 5 225H (14 nhân, 18 luồng, tối đa 5.0GHz)', '32GB LPDDR5x 8533MHz, onboard', '1TB SSD NVMe, 1 slot', 'Intel Arc 130T GPU', '14.5" 3K (3072x1920), 120Hz, 500 nits, 100% DCI-P3', '60Wh', '2 loa, Dolby Atmos', '2 USB-C 4.0, 1 USB-A 3.2, HDMI 2.0, jack 3.5mm', 'Wi-Fi 6E, Bluetooth 5.3', '1.4kg', 'Xanh dương', 'New 100%', '24 tháng tại Lenovo', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core Ultra 5 225H<br>-RAM: 32GB LPDDR5x 8533MHz<br>-Màn hình: 14.5" 3K (3072x1920), ~500nits<br>-Đồ họa: Intel Arc 130T'),
(5, 'Intel Core i7 14650HX (14 nhân 24 luồng, tới 5.2GHZ)', '16GB RAM DDR5 5600MHZ hỗ trợ nâng cấp, 2 khe lắp ram', '1TB PCIe Gen5 SSD, hỗ trợ nâng cấp, 2 slot SSD', 'NVIDIA®GeForce® RTX™ 5060 8GB GDDR7', '16" 2.5K (2560x1600) IPS nhám, 500nits, 100% sRGB, 240Hz', '83Wh', '2 loa nằm ở 2 mé cạnh đáy trái phải', '2 cổng USB-A 3.2 Gen 1, 1 USB-A 3.2 Gen 2, 1 USB-C 3.2 Gen 2', 'Wi-Fi® 6E, Bluetooth 5.3', '~2.43kg', 'Đen', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 14650HX<br>-RAM: 16GB DDR5 5600MHz<br>-Màn hình: 16" 2.5K 240Hz<br>-Đồ họa: NVIDIA RTX 4060'),
(6, 'AMD Ryzen AI 9 365 (12 nhân, 24 luồng, tối đa 5.2GHz)', '32GB LPDDR5x 8000MHz, onboard', '1TB SSD NVMe, 1 slot', 'AMD Radeon 880M', '14" 2.8K (2880x1800) OLED, 120Hz, 400 nits, 100% sRGB', '70Wh', '2 loa, Dolby Atmos', '2 USB-C 4.0, 1 USB-A 3.2, HDMI 2.1, jack 3.5mm', 'Wi-Fi 7, Bluetooth 5.3', '1.5kg', 'Bạc', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: AMD Ryzen AI 9 365<br>-RAM: 32GB LPDDR5x 8000 onboard<br>-Màn hình: 14", 2.8K (2880x1800) OLED<br>-Đồ họa: AMD Radeon 880M'),
(7, 'AMD Ryzen 7 H 255 (8 nhân, 16 luồng, tối đa 4.9GHz)', '24GB DDR5 4800MHz, 2 khe, hỗ trợ nâng cấp', '1TB SSD NVMe, 1 slot', 'AMD Radeon 780M', '14" 2.8K (2880x1800) OLED, 120Hz, 400 nits, 100% sRGB', '55Wh', '2 loa, Dolby Audio', '1 USB-C, 2 USB-A 3.0, HDMI 1.4, jack 3.5mm', 'Wi-Fi 6, Bluetooth 5.2', '1.6kg', 'Xám', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: AMD Ryzen 7 H 255<br>-RAM: 24GB DDR5 4800MHz<br>-Màn hình: 14", 2.8K (2880x1800) OLED<br>-Đồ họa: AMD Radeon 780M'),
(8, 'Intel Core i9 14900HX (24 nhân, 32 luồng, tối đa 5.4GHz)', '16GB DDR5 5600MHz, 2 khe, hỗ trợ nâng cấp', '1TB SSD NVMe, 2 slots, hỗ trợ mở rộng', 'NVIDIA GeForce RTX 5060 8GB GDDR6', '16" 2.5K (2560x1600), 240Hz, 500 nits, 100% sRGB', '80Wh', '2 loa, Nahimic Audio', '2 USB-C 4.0, 2 USB-A 3.2, HDMI 2.1, jack 3.5mm', 'Wi-Fi 6E, Bluetooth 5.3', '2.4kg', 'Đen', 'New 100%', '24 tháng tại Lenovo', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i9 14900HX<br>-RAM: 16GB DDR5 5600MHz<br>-Màn hình: 16" 2.5K (2560x1600), 240Hz<br>-Đồ họa: NVIDIA RTX 5060'),
(9, 'Intel Core Ultra 5 225H (14 nhân, 18 luồng, tối đa 5.0GHz)', '32GB LPDDR5x 8533MHz, onboard', '1TB SSD NVMe, 1 slot', 'Intel Arc 130T GPU', '16" 2.8K (2880x1920) OLED, 120Hz, 500 nits, 100% DCI-P3', '70Wh', '2 loa, Dolby Atmos', '2 USB-C 4.0, 1 USB-A 3.2, HDMI 2.0, jack 3.5mm', 'Wi-Fi 6E, Bluetooth 5.3', '1.8kg', 'Xanh lá', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core Ultra 5 225H<br>-RAM: 32GB LPDDR5x 8533 onboard<br>-Màn hình: 16", 2.8K (2880x1800) OLED<br>-Đồ họa: Intel Arc 130T'),
(10, 'Intel Core i5 13420H (8 nhân, 12 luồng, tối đa 4.8GHz)', '16GB DDR5 5200MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 1 slot, hỗ trợ mở rộng', 'Nvidia GeForce RTX 4050 6GB GDDR6', '16" FHD+ (1920x1200) IPS, 165Hz, 300 nits, 72% NTSC', '65Wh', '2 loa, DTS:X Ultra', '1 USB-C 3.2 Gen 2, 2 USB-A 3.2 Gen 1, HDMI 2.1, jack 3.5mm', 'Wi-Fi 6E, Bluetooth 5.2', '2.2kg', 'Xám', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 13420H<br>-RAM: 16GB DDR5 5200MHz<br>-Màn hình: 16" FHD+ (1920x1200) IPS, 165Hz<br>-Đồ họa: Nvidia GeForce RTX 4050 6GB'),
(11, 'Intel Core i7 14650HX (16 nhân, 24 luồng, tối đa 5.2GHz)', '16GB DDR5 5600MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 2 slots, hỗ trợ mở rộng', 'NVIDIA GeForce RTX 5060 8GB GDDR6', '15.3" 2.5K (2560x1600), 180Hz, 400 nits, 100% sRGB', '75Wh', '2 loa, Nahimic Audio', '1 USB-C 4.0, 2 USB-A 3.2, HDMI 2.1, jack 3.5mm', 'Wi-Fi 6E, Bluetooth 5.3', '2.3kg', 'Xám', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 14650HX<br>-RAM: 16GB DDR5 5600MHz<br>-Màn hình: 15.3" 2.5K (2560x1600), 180Hz<br>-Đồ họa: NVIDIA RTX 5060'),
(12, 'AMD Ryzen 9 8945HX (12 nhân, 24 luồng, tối đa 5.4GHz)', '32GB DDR5 5200MHz, 2 khe, hỗ trợ nâng cấp', '1TB SSD NVMe, 2 slots, hỗ trợ mở rộng', 'NVIDIA GeForce RTX 5060 8GB GDDR6', '16" 2.5K (2560x1600), 240Hz, 500 nits, 100% sRGB', '80Wh', '2 loa, Nahimic Audio', '2 USB-C 4.0, 2 USB-A 3.2, HDMI 2.1, jack 3.5mm', 'Wi-Fi 7, Bluetooth 5.3', '2.5kg', 'Đen', 'New 100%', '24 tháng tại Lenovo', 'Chi Tiết Cấu Hình<br>-CPU: AMD Ryzen 9 8945HX<br>-RAM: 32GB DDR5 5200MHz<br>-Màn hình: 16" (2560x1600), 240Hz, 500nits<br>-Đồ họa: NVIDIA RTX 5060'),
(13, 'Intel Core i5 13420H (8 nhân, 12 luồng, tối đa 4.7GHz)', '16GB DDR5 4800MHz, 1 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 1 slot, hỗ trợ mở rộng', 'Intel UHD Graphics', '15.1" 2.5K (2560x1600) OLED, 165Hz, 500 nits, 100% sRGB', '45Wh', '2 loa, Dolby Audio', '1 USB-C, 2 USB-A 3.0, HDMI 1.4, jack 3.5mm', 'Wi-Fi 5, Bluetooth 5.0', '1.7kg', 'Xám bạc', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 13420H<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 15.1", 2.5K (2560x1600) OLED, 500nits<br>-Đồ họa: Intel UHD Graphics'),
(14, 'Intel Core Ultra 5 225H (14 nhân, 18 luồng, tối đa 5.0GHz)', '32GB LPDDR5x 8533MHz, onboard', '1TB SSD NVMe, 1 slot', 'Intel Arc 130T GPU', '14.5" 3K (3072x1920), 120Hz, 500 nits, 100% DCI-P3', '60Wh', '2 loa, Dolby Atmos', '2 USB-C 4.0, 1 USB-A 3.2, HDMI 2.0, jack 3.5mm', 'Wi-Fi 6E, Bluetooth 5.3', '1.4kg', 'Xanh dương', 'New 100%', '36 tháng tại Lenovo', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core Ultra 5 225H<br>-RAM: 32GB LPDDR5x 8533MHz<br>-Màn hình: 14.5" 3K (3072x1920), ~500nits<br>-Đồ họa: Intel Arc 130T'),
(15, 'Apple M2 Pro 10 core (8 hiệu năng, 2 tiết kiệm)', '16GB unified memory, onboard', '512GB SSD, không hỗ trợ mở rộng', 'Apple M2 GPU 16 core', '14.2" Liquid Retina XDR (3024x1964), 120Hz, 1000 nits', '70Wh', '6 loa, Spatial Audio', '3 Thunderbolt 4, HDMI, jack 3.5mm', 'Wi-Fi 6, Bluetooth 5.0', '1.6kg', 'Xám không gian', 'New 100%', '12 tháng tại Apple', 'Chi Tiết Cấu Hình<br>-CPU: Apple M2 Pro 10 core<br>-RAM: 16GB<br>-Màn hình: 14.2" 3K Liquid Retina XDR (3024x1964)<br>-Đồ họa: Apple M2 GPU 16 core'),
(16, 'Apple M1 Pro 10 core (8 hiệu năng, 2 tiết kiệm)', '16GB unified memory, onboard', '512GB SSD, không hỗ trợ mở rộng', 'Apple M1 Pro GPU 16 core', '16.2" Liquid Retina XDR (3456x2234), 120Hz, 1000 nits', '75Wh', '6 loa, Spatial Audio', '3 Thunderbolt 4, HDMI, jack 3.5mm', 'Wi-Fi 6, Bluetooth 5.0', '2.1kg', 'Bạc', 'New 100%', '12 tháng tại Apple', 'Chi Tiết Cấu Hình<br>-CPU: M1 Pro 10 core<br>-RAM: 16GB<br>-Màn hình: 16.2" Liquid Retina XDR (3456x2234)<br>-Đồ họa: Apple M1 Pro GPU 16 core'),
(17, 'Apple M1 Pro 10 core (8 hiệu năng, 2 tiết kiệm)', '16GB unified memory, onboard', '512GB SSD, không hỗ trợ mở rộng', 'Apple M1 Pro GPU 16 core', '14" Liquid Retina XDR (3024x1964), 120Hz, 1000 nits', '70Wh', '6 loa, Spatial Audio', '3 Thunderbolt 4, HDMI, jack 3.5mm', 'Wi-Fi 6, Bluetooth 5.0', '1.6kg', 'Xám không gian', 'New 100%', '12 tháng tại Apple', 'Chi Tiết Cấu Hình<br>-CPU: M1 Pro 10 core<br>-RAM: 16GB<br>-Màn hình: Liquid Retina XDR (3024x1964)<br>-Đồ họa: Apple M1 Pro GPU 16 core'),
(18, 'Apple M1 Pro 8 core (6 hiệu năng, 2 tiết kiệm)', '16GB unified memory, onboard', '512GB SSD, không hỗ trợ mở rộng', 'Apple M1 Pro GPU 14 core', '14" Liquid Retina XDR (3024x1964), 120Hz, 1000 nits', '70Wh', '6 loa, Spatial Audio', '3 Thunderbolt 4, HDMI, jack 3.5mm', 'Wi-Fi 6, Bluetooth 5.0', '1.6kg', 'Bạc', 'Like New 99%', '3 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: M1 Pro 8 core<br>-RAM: 16GB<br>-Màn hình: Liquid Retina XDR (3024x1964)<br>-Đồ họa: Apple M1 Pro GPU 14 core'),
(19, 'Apple M1 Pro 10 core (8 hiệu năng, 2 tiết kiệm)', '16GB unified memory, onboard', '512GB SSD, không hỗ trợ mở rộng', 'Apple M1 Pro GPU 16 core', '16.2" Liquid Retina XDR (3456x2234), 120Hz, 1000 nits', '75Wh', '6 loa, Spatial Audio', '3 Thunderbolt 4, HDMI, jack 3.5mm', 'Wi-Fi 6, Bluetooth 5.0', '2.1kg', 'Bạc', 'New 100%', '12 tháng tại Apple', 'Chi Tiết Cấu Hình<br>-CPU: M1 Pro 10 core<br>-RAM: 16GB<br>-Màn hình: 16.2" Liquid Retina XDR (3456x2234)<br>-Đồ họa: Apple M1 Pro GPU 16 core'),
(20, 'acer nitroV sieu cap', '16GB DDR5', '512GB SSD', 'RTX 4050', '15.6" FHD 144Hz', '57Wh', 'DTS:X', 'USB-C, USB-A', 'Wi-Fi 6', '2.1kg', 'Đen', 'New', '12 tháng', 'cấu hình siêu khủng, cân hết mọi tựa game'),
(21, 'Dell Precision 5580', '32GB DDR5', '1TB SSD', 'RTX A1000', '15.6" FHD IPS', '86Wh', 'Stereo', 'Thunderbolt', 'Wi-Fi 6', '1.9kg', 'Xám', 'New', '12 tháng', 'Cấu hình siêu khủng, phù hợp cho việc làm đồ họa 24/24'),
(22, 'acer nitroV', '8GB DDR5', '512GB SSD', 'RTX 2050', '15.6" FHD 144Hz', '57Wh', 'DTS:X', 'USB-C, USB-A', 'Wi-Fi 6', '2.1kg', 'Đen', 'New', '12 tháng', 'abcbcsds'),
(101, 'Intel Core i7 13700HX (16 nhân, 24 luồng, tối đa 5.0GHz)', '16GB DDR5 4800MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 2 slot', 'NVIDIA GeForce RTX 4060 8GB GDDR6', '16" WQXGA (2560x1600) 165Hz, 500 nits, 100% sRGB', '90Wh', 'DTS:X Ultra', '2x USB-C 3.2, 3x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6E, Bluetooth 5.2', '2.6kg', 'Đen', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 13700HX<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 16" 2.5K 165Hz<br>-Đồ họa: NVIDIA RTX 4060 8GB<br>-Nhu cầu: Gaming / Đồ họa'),
(102, 'Intel Core i5 13420H (8 nhân, 12 luồng, tối đa 4.6GHz)', '16GB DDR5 5200MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 2 slot', 'NVIDIA GeForce RTX 4050 6GB GDDR6', '15.6" FHD (1920x1080) 144Hz, 250 nits', '57Wh', 'DTS:X Ultra', '1x USB-C 3.2, 3x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6, Bluetooth 5.1', '2.11kg', 'Đen', 'New 100%', '12 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 13420H<br>-RAM: 16GB DDR5 5200MHz<br>-Màn hình: 15.6" FHD 144Hz<br>-Đồ họa: NVIDIA RTX 4050 6GB<br>-Nhu cầu: Gaming / Học tập'),
(103, 'Intel Core Ultra 5 125H (14 nhân, 18 luồng)', '16GB LPDDR5X 6400MHz, onboard', '512GB SSD NVMe, 1 slot', 'Intel Arc Graphics', '14" 2.8K OLED (2880x1800) 90Hz, 400 nits, 100% DCI-P3', '65Wh', 'Acer TrueHarmony', '2x Thunderbolt 4, 2x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6E, Bluetooth 5.3', '1.32kg', 'Bạc', 'New 100%', '12 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core Ultra 5 125H<br>-RAM: 16GB LPDDR5X<br>-Màn hình: 14" 2.8K OLED 90Hz<br>-Đồ họa: Intel Arc Graphics<br>-Nhu cầu: Văn phòng / Lập trình nhẹ'),
(104, 'AMD Ryzen 9 7940HS (8 nhân, 16 luồng, tối đa 5.2GHz)', '16GB DDR5 4800MHz, onboard', '1TB SSD NVMe, 1 slot', 'NVIDIA GeForce RTX 4060 8GB GDDR6', '14" QHD+ (2560x1600) 165Hz, 500 nits, 100% DCI-P3', '76Wh', '4 loa, Dolby Atmos', '2x USB-C 3.2, 2x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6E, Bluetooth 5.3', '1.65kg', 'Xám', 'New 100%', '24 tháng tại hãng', 'Chi Tiết Cấu Hình<br>-CPU: AMD Ryzen 9 7940HS<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 14" QHD+ 165Hz<br>-Đồ họa: NVIDIA RTX 4060 8GB<br>-Nhu cầu: Gaming / Lập trình'),
(105, 'AMD Ryzen 7 7735HS (8 nhân, 16 luồng, tối đa 4.7GHz)', '16GB DDR5 4800MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 2 slot', 'NVIDIA GeForce RTX 4050 6GB GDDR6', '15.6" FHD (1920x1080) 144Hz, 100% sRGB', '90Wh', 'Dolby Atmos', '1x USB-C 4.0, 1x USB-C 3.2, 2x USB-A 3.2', 'Wi-Fi 6, Bluetooth 5.2', '2.2kg', 'Xám đen', 'New 100%', '24 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: AMD Ryzen 7 7735HS<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 15.6" FHD 144Hz<br>-Đồ họa: NVIDIA RTX 4050 6GB<br>-Nhu cầu: Gaming / Học tập'),
(106, 'Intel Core i7 1355U (10 nhân, 12 luồng, tối đa 5.0GHz)', '16GB LPDDR5 5200MHz, onboard', '1TB SSD NVMe', 'Intel Iris Xe Graphics', '13.3" 2.8K OLED (2880x1800) 60Hz, 550 nits', '63Wh', 'Harman Kardon, Dolby Atmos', '2x Thunderbolt 4, 1x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6E, Bluetooth 5.3', '1.0kg', 'Xanh đen', 'New 100%', '24 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 1355U<br>-RAM: 16GB LPDDR5<br>-Màn hình: 13.3" 2.8K OLED<br>-Đồ họa: Intel Iris Xe<br>-Nhu cầu: Văn phòng / Lập trình'),
(107, 'Intel Core i7 13700H (14 nhân, 20 luồng, tối đa 5.0GHz)', '16GB DDR5 4800MHz, 2 khe, hỗ trợ nâng cấp', '1TB SSD NVMe, 2 slot', 'NVIDIA GeForce RTX 4050 6GB GDDR6', '15.6" FHD+ (1920x1200), 500 nits, 100% sRGB', '86Wh', 'Studio Quality, Waves Nx 3D', '2x Thunderbolt 4, 1x USB-C 3.2', 'Wi-Fi 6, Bluetooth 5.3', '1.92kg', 'Bạc', 'New 100%', '12 tháng tại D-computer', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 13700H<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 15.6" FHD+ 500 nits<br>-Đồ họa: NVIDIA RTX 4050 6GB<br>-Nhu cầu: Đồ họa / Lập trình'),
(108, 'Intel Core i7 13700H (14 nhân, 20 luồng)', '16GB LPDDR5 4800MHz, onboard', '1TB SSD NVMe', 'NVIDIA GeForce RTX 3050 6GB GDDR6', '16.0" 2.5K (2560x1600) 120Hz, 300 nits, 100% sRGB', '86Wh', 'Waves MaxxAudio Pro', '1x Thunderbolt 4, 2x USB-A 3.2, HDMI 2.0', 'Wi-Fi 6E, Bluetooth 5.2', '2.06kg', 'Bạc', 'New 100%', '12 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 13700H<br>-RAM: 16GB LPDDR5<br>-Màn hình: 16" 2.5K 120Hz<br>-Đồ họa: NVIDIA RTX 3050 6GB<br>-Nhu cầu: Văn phòng / Lập trình'),
(109, 'Intel Core Ultra 7 155H (16 nhân, 22 luồng)', '16GB DDR5 5600MHz, 2 khe, hỗ trợ nâng cấp', '1TB SSD NVMe', 'NVIDIA GeForce RTX 4070 8GB GDDR6', '16.0" QHD+ (2560x1600) 240Hz, 100% sRGB', '90Wh', 'Alienware Sound', '2x Thunderbolt 4, 2x USB-A 3.2, HDMI 2.1, RJ45', 'Wi-Fi 7, Bluetooth 5.4', '2.61kg', 'Đen ánh kim', 'New 100%', '12 tháng cao cấp', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core Ultra 7 155H<br>-RAM: 16GB DDR5 5600MHz<br>-Màn hình: 16" QHD+ 240Hz<br>-Đồ họa: NVIDIA RTX 4070 8GB<br>-Nhu cầu: Gaming / Đồ họa'),
(110, 'Intel Core i7 13700H (14 nhân, 20 luồng, tối đa 5.0GHz)', '16GB DDR5 5200MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 2 slot', 'NVIDIA GeForce RTX 4060 8GB GDDR6', '16" WQXGA (2560x1600) 165Hz, 300 nits, 100% sRGB', '80Wh', '2 loa, Nahimic Audio', '2x USB-C 3.2, 2x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6E, Bluetooth 5.1', '2.4kg', 'Xám', 'New 100%', '24 tháng tại Lenovo', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 13700H<br>-RAM: 16GB DDR5 5200MHz<br>-Màn hình: 16" 2.5K 165Hz<br>-Đồ họa: NVIDIA RTX 4060 8GB<br>-Nhu cầu: Gaming / Lập trình'),
(111, 'Intel Core i7 13650HX (14 nhân, 20 luồng)', '16GB DDR5 4800MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe', 'NVIDIA GeForce RTX 4050 6GB GDDR6', '15.6" FHD (1920x1080) 144Hz, 100% sRGB', '60Wh', 'Nahimic Audio', '1x USB-C 3.2, 3x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6, Bluetooth 5.1', '2.38kg', 'Xám', 'New 100%', '24 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i7 13650HX<br>-RAM: 16GB DDR5 4800MHz<br>-Màn hình: 15.6" FHD 144Hz<br>-Đồ họa: NVIDIA RTX 4050 6GB<br>-Nhu cầu: Gaming / Học tập'),
(112, 'Intel Core i5 1335U (10 nhân, 12 luồng)', '16GB LPDDR5x 4800MHz, onboard', '512GB SSD NVMe', 'Intel Iris Xe Graphics', '14.0" WUXGA (1920x1200) IPS, 300 nits, chống chói', '52.5Wh', 'Dolby Audio', '2x Thunderbolt 4, 2x USB-A 3.2, HDMI 2.1, RJ45', 'Wi-Fi 6E, Bluetooth 5.3', '1.36kg', 'Đen', 'New 100%', '36 tháng Premier Support', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 1335U<br>-RAM: 16GB LPDDR5x<br>-Màn hình: 14" WUXGA IPS<br>-Đồ họa: Intel Iris Xe<br>-Nhu cầu: Lập trình / Văn phòng'),
(113, 'AMD Ryzen 7 7840HS (8 nhân, 16 luồng, tối đa 5.1GHz)', '16GB DDR5 5600MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe, 2 slot', 'NVIDIA GeForce RTX 4060 8GB GDDR6', '16.1" FHD (1920x1080) 165Hz, 300 nits, 100% sRGB', '83Wh', 'Bang & Olufsen, DTS:X', '2x USB-C 3.2, 2x USB-A 3.2, HDMI 2.1', 'Wi-Fi 6E, Bluetooth 5.3', '2.37kg', 'Đen', 'New 100%', '12 tháng tại hãng', 'Chi Tiết Cấu Hình<br>-CPU: AMD Ryzen 7 7840HS<br>-RAM: 16GB DDR5 5600MHz<br>-Màn hình: 16.1" FHD 165Hz<br>-Đồ họa: NVIDIA RTX 4060 8GB<br>-Nhu cầu: Gaming / Đồ họa'),
(114, 'Intel Core i5 13500H (12 nhân, 16 luồng)', '16GB DDR5 5200MHz, 2 khe, hỗ trợ nâng cấp', '512GB SSD NVMe', 'NVIDIA GeForce RTX 4050 6GB GDDR6', '16.1" FHD (1920x1080) 144Hz, 250 nits', '70Wh', 'B&O Audio', '1x USB-C 3.2, 3x USB-A 3.2, HDMI 2.1, RJ45', 'Wi-Fi 6E, Bluetooth 5.3', '2.33kg', 'Xanh đen', 'New 100%', '12 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core i5 13500H<br>-RAM: 16GB DDR5 5200MHz<br>-Màn hình: 16.1" FHD 144Hz<br>-Đồ họa: NVIDIA RTX 4050 6GB<br>-Nhu cầu: Gaming / Học tập'),
(115, 'Intel Core Ultra 7 155U (12 nhân, 14 luồng)', '16GB LPDDR5 6400MHz, onboard', '1TB SSD NVMe', 'Intel Graphics', '14.0" WUXGA (1920x1200) IPS Cảm ứng, 300 nits', '59Wh', 'Poly Studio, DTS:X', '2x Thunderbolt 4, 2x USB-A 3.2, HDMI 2.1', 'Wi-Fi 7, Bluetooth 5.4', '1.39kg', 'Bạc', 'New 100%', '12 tháng chính hãng', 'Chi Tiết Cấu Hình<br>-CPU: Intel Core Ultra 7 155U<br>-RAM: 16GB LPDDR5 6400MHz<br>-Màn hình: 14" WUXGA Cảm ứng<br>-Đồ họa: Intel Graphics<br>-Nhu cầu: Văn phòng / Doanh nhân'),
(116, 'Apple M3 (8-core CPU)', '16GB Unified Memory, onboard', '512GB SSD, không hỗ trợ nâng cấp', '10-core GPU', '15.3" Liquid Retina (2880x1864), 500 nits', '66.5Wh', '6 loa, Spatial Audio', '2x Thunderbolt / USB 4, MagSafe 3', 'Wi-Fi 6E, Bluetooth 5.3', '1.51kg', 'Starlight', 'New 100%', '12 tháng tại Apple', 'Chi Tiết Cấu Hình<br>-CPU: Apple M3 8-core<br>-RAM: 16GB Unified<br>-Màn hình: 15.3" Liquid Retina<br>-Đồ họa: 10-core GPU<br>-Nhu cầu: Văn phòng / Lập trình'),
(117, 'Apple M3 (8-core CPU)', '8GB Unified Memory, onboard', '256GB SSD, không hỗ trợ nâng cấp', '8-core GPU', '13.6" Liquid Retina (2560x1664), 500 nits', '52.6Wh', '4 loa, Spatial Audio', '2x Thunderbolt / USB 4, MagSafe 3', 'Wi-Fi 6E, Bluetooth 5.3', '1.24kg', 'Midnight', 'New 100%', '12 tháng tại Apple', 'Chi Tiết Cấu Hình<br>-CPU: Apple M3 8-core<br>-RAM: 8GB Unified<br>-Màn hình: 13.6" Liquid Retina<br>-Đồ họa: 8-core GPU<br>-Nhu cầu: Văn phòng / Học tập'),
(118, 'Apple M3 Max (16-core CPU)', '48GB Unified Memory, onboard', '1TB SSD, không hỗ trợ nâng cấp', '40-core GPU', '16.2" Liquid Retina XDR (3456x2234) 120Hz, 1000 nits', '100Wh', '6 loa, Spatial Audio', '3x Thunderbolt 4, HDMI, SDXC, MagSafe 3', 'Wi-Fi 6E, Bluetooth 5.3', '2.16kg', 'Space Black', 'New 100%', '12 tháng tại Apple', 'Chi Tiết Cấu Hình<br>-CPU: Apple M3 Max 16-core<br>-RAM: 48GB Unified<br>-Màn hình: 16.2" Liquid Retina XDR 120Hz<br>-Đồ họa: 40-core GPU<br>-Nhu cầu: Đồ họa / Lập trình nặng')
ON CONFLICT (product_id) DO NOTHING;

-- 4. Seed Product Images
INSERT INTO product_images (product_id, image_url) VALUES 
(1, 'assets/Dell_gaming_G15_5530_img0.jpg'), (1, 'assets/Dell_gaming_G15_5530_img1.jpg'), (1, 'assets/Dell_gaming_G15_5530_img2.jpg'), (1, 'assets/Dell_gaming_G15_5530_img3.jpg'), (1, 'assets/Dell_gaming_G15_5530_img4.jpg'),
(2, 'assets/gigabyte_gaming_a16_img0.png'), (2, 'assets/gigabyte_gaming_a16_img1.png'), (2, 'assets/gigabyte_gaming_a16_img2.png'), (2, 'assets/gigabyte_gaming_a16_img3.png'), (2, 'assets/gigabyte_gaming_a16_img4.png'),
(3, 'assets/ideapad_slim3_15irh10_img0.png'), (3, 'assets/ideapad_slim3_15irh10_img1.png'), (3, 'assets/ideapad_slim3_15irh10_img2.png'), (3, 'assets/ideapad_slim3_15irh10_img3.png'), (3, 'assets/ideapad_slim3_15irh10_img4.png'),
(4, 'assets/thinkbook_14_g7_img0.jpg'), (4, 'assets/thinkbook_14_g7_img1.jpg'), (4, 'assets/thinkbook_14_g7_img2.jpg'), (4, 'assets/thinkbook_14_g7_img3.jpg'), (4, 'assets/thinkbook_14_g7_img4.jpg'),
(5, 'assets/acer_sadow_desc_img0.png'), (5, 'assets/acer_shadow_desc_img2.png'), (5, 'assets/acer_shadow_desc_img3.png'), (5, 'assets/acer_sadow_desc_img4.png'), (5, 'assets/acer_sadow_desc_img5.png'),
(6, 'assets/ideapad_5pro_14gt_img0.jpg'), (6, 'assets/ideapad_5pro_14gt_img1.jpg'), (6, 'assets/ideapad_5pro_14gt_img2.jpg'), (6, 'assets/ideapad_5pro_14gt_img3.jpg'), (6, 'assets/ideapad_5pro_14gt_img4.jpg'),
(7, 'assets/ideapad_slim5_2025_img0.png'), (7, 'assets/ideapad_slim5_2025_img1.png'), (7, 'assets/ideapad_slim5_2025_img2.png'), (7, 'assets/ideapad_slim5_2025_img3.png'), (7, 'assets/ideapad_slim5_2025_img4.png'),
(8, 'assets/y7000_2025_img0.jpg'), (8, 'assets/y7000_2025_img1.jpg'), (8, 'assets/y7000_2025_img2.jpg'), (8, 'assets/y7000_2025_img3.jpg'), (8, 'assets/y7000_2025_img4.jpg'),
(9, 'assets/ideapad_5pro_16gt_img0.jpg'), (9, 'assets/ideapad_5pro_16gt_img1.jpg'), (9, 'assets/ideapad_5pro_16gt_img2.jpg'), (9, 'assets/ideapad_5pro_16gt_img3.jpg'), (9, 'assets/ideapad_5pro_16gt_img4.jpg'),
(10, 'assets/gigabyte_gaming_a16_img0.png'), (10, 'assets/gigabyte_gaming_a16_img1.png'), (10, 'assets/gigabyte_gaming_a16_img2.png'), (10, 'assets/gigabyte_gaming_a16_img3.png'), (10, 'assets/gigabyte_gaming_a16_img4.png'),
(11, 'assets/y7000_2025_img0.jpg'), (11, 'assets/y7000_2025_img1.jpg'), (11, 'assets/y7000_2025_img2.jpg'), (11, 'assets/y7000_2025_img3.jpg'), (11, 'assets/y7000_2025_img4.jpg'),
(12, 'assets/legion_pro5_r9000p_img0.jpg'), (12, 'assets/legion_pro5_r9000p_img1.jpg'), (12, 'assets/legion_pro5_r9000p_img2.jpg'), (12, 'assets/legion_pro5_r9000p_img3.jpg'), (12, 'assets/legion_pro5_r9000p_img4.jpg'),
(13, 'assets/ideapad_slim3_15irh10_img0.png'), (13, 'assets/ideapad_slim3_15irh10_img1.png'), (13, 'assets/ideapad_slim3_15irh10_img2.png'), (13, 'assets/ideapad_slim3_15irh10_img3.png'), (13, 'assets/ideapad_slim3_15irh10_img4.png'),
(14, 'assets/thinkbook_14_g7_img0.jpg'), (14, 'assets/thinkbook_14_g7_img1.jpg'), (14, 'assets/thinkbook_14_g7_img2.jpg'), (14, 'assets/thinkbook_14_g7_img3.jpg'), (14, 'assets/thinkbook_14_g7_img4.jpg'),
(15, 'assets/macbook_pro14_M2_img0.jpg'), (15, 'assets/macbook_pro14_M2_img1.jpg'), (15, 'assets/macbook_pro14_M2_img2.jpg'), (15, 'assets/macbook_pro14_M2_img3.jpg'), (15, 'assets/macbook_pro14_M2_img4.jpg'),
(16, 'assets/macbook_pro_16m1_img0.jpg'), (16, 'assets/macbook_pro_16m1_img1.jpg'), (16, 'assets/macbook_pro_16m1_img2.jpg'), (16, 'assets/macbook_pro_16m1_img3.jpg'), (16, 'assets/macbook_pro_16m1_img4.jpg'),
(17, 'assets/macbook_pro_14_m1_img0.png'), (17, 'assets/macbook_pro_14_m1_img1.png'), (17, 'assets/macbook_pro_14_m1_img2.png'), (17, 'assets/macbook_pro_14_m1_img3.png'), (17, 'assets/macbook_pro_14_m1_img4.png'),
(18, 'assets/macbook_pro_14_m1_img0.png'), (18, 'assets/macbook_pro_14_m1_img1.png'), (18, 'assets/macbook_pro_14_m1_img2.png'), (18, 'assets/macbook_pro_14_m1_img3.png'), (18, 'assets/macbook_pro_14_m1_img4.png'),
(19, 'assets/macbook_pro_16m1_img0.jpg'), (19, 'assets/macbook_pro_16m1_img1.jpg'), (19, 'assets/macbook_pro_16m1_img2.jpg'), (19, 'assets/macbook_pro_16m1_img3.jpg'), (19, 'assets/macbook_pro_16m1_img4.jpg'),
(20, 'assets/idea_padpro_14gt.jpg'), (21, 'assets/dohoakythuat.webp'), (22, 'assets/acer_sadow_desc_img0.png'),
(101, 'assets/acer_helios_neo_16_img0.jpg'), (101, 'assets/acer_helios_neo_16_img1.jpg'), (101, 'assets/acer_helios_neo_16_img2.jpg'), 
(102, 'assets/acer_nitro_v15_img0.jpg'), (102, 'assets/acer_nitro_v15_img1.jpg'), (102, 'assets/acer_nitro_v15_img2.jpg'), 
(103, 'assets/acer_swift_go14_img0.jpg'), (103, 'assets/acer_swift_go14_img1.jpg'), (103, 'assets/acer_swift_go14_img2.jpg'), 
(104, 'assets/asus_rog_g14_img0.jpg'), (104, 'assets/asus_rog_g14_img1.jpg'), (104, 'assets/asus_rog_g14_img2.jpg'), 
(105, 'assets/asus_tuf_a15_img0.jpg'), (105, 'assets/asus_tuf_a15_img1.jpg'), (105, 'assets/asus_tuf_a15_img2.jpg'), 
(106, 'assets/asus_zenbook_s13_img0.jpg'), (106, 'assets/asus_zenbook_s13_img1.jpg'), (106, 'assets/asus_zenbook_s13_img2.jpg'), 
(107, 'assets/dell_xps_15_img0.jpg'), (107, 'assets/dell_xps_15_img1.jpg'), (107, 'assets/dell_xps_15_img2.jpg'), 
(108, 'assets/dell_inspiron_16_img0.jpg'), (108, 'assets/dell_inspiron_16_img1.jpg'), (108, 'assets/dell_inspiron_16_img2.jpg'), 
(109, 'assets/dell_alienware_m16_img0.jpg'), (109, 'assets/dell_alienware_m16_img1.jpg'), (109, 'assets/dell_alienware_m16_img2.jpg'), 
(110, 'assets/lenovo_legion_slim5_img0.jpg'), (110, 'assets/lenovo_legion_slim5_img1.jpg'), (110, 'assets/lenovo_legion_slim5_img2.jpg'), 
(111, 'assets/lenovo_loq_15_img0.jpg'), (111, 'assets/lenovo_loq_15_img1.jpg'), (111, 'assets/lenovo_loq_15_img2.jpg'), 
(112, 'assets/lenovo_thinkpad_t14_img0.jpg'), (112, 'assets/lenovo_thinkpad_t14_img1.jpg'), (112, 'assets/lenovo_thinkpad_t14_img2.jpg'), 
(113, 'assets/hp_omen_16_img0.jpg'), (113, 'assets/hp_omen_16_img1.jpg'), (113, 'assets/hp_omen_16_img2.jpg'), 
(114, 'assets/hp_victus_16_img0.jpg'), (114, 'assets/hp_victus_16_img1.jpg'), (114, 'assets/hp_victus_16_img2.jpg'), 
(115, 'assets/hp_envy_x360_img0.jpg'), (115, 'assets/hp_envy_x360_img1.jpg'), (115, 'assets/hp_envy_x360_img2.jpg'), 
(116, 'assets/macbook_air_15_m3_img0.jpg'), (116, 'assets/macbook_air_15_m3_img1.jpg'), (116, 'assets/macbook_air_15_m3_img2.jpg'),
(117, 'assets/macbook_air_13_m3_img0.jpg'), (117, 'assets/macbook_air_13_m3_img1.jpg'), (117, 'assets/macbook_air_13_m3_img2.jpg'),
(118, 'assets/macbook_pro_16_m3max_img0.jpg'), (118, 'assets/macbook_pro_16_m3max_img1.jpg'), (118, 'assets/macbook_pro_16_m3max_img2.jpg')
ON CONFLICT (id) DO NOTHING;

-- Thiết lập lại sequence cho product_images
SELECT setval('product_images_id_seq', COALESCE((SELECT MAX(id)+1 FROM product_images), 1), false);

-- 5. Seed Users
-- Mật khẩu mặc định cho cả 2 tài khoản: Abc123@ (được hash BCrypt)
INSERT INTO users (full_name, email, phone, password, address, role) VALUES
('User Seed', 'taobattu@gmail.com', '0900000001', '$2a$10$iXlZZiuvjLbNnfnbd7MBr.Ree1WyT7l6V7tiAwKyf0iMcFf234kHm', '123 Đường Láng, Hà Nội', 'USER'),
('Admin Seed', 'Admin@gmail.com', '0900000002', '$2a$10$iXlZZiuvjLbNnfnbd7MBr.Ree1WyT7l6V7tiAwKyf0iMcFf234kHm', 'Hà Nội, Việt Nam', 'ADMIN')
ON CONFLICT (email) DO NOTHING;

-- Thiết lập lại sequence cho users
SELECT setval('users_id_seq', COALESCE((SELECT MAX(id)+1 FROM users), 1), false);
