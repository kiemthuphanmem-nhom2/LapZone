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
