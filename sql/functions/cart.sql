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
