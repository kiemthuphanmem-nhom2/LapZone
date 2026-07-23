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
