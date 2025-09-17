-- QR Code Ordering System Database Schema
-- This file contains the complete database schema with tables, enums, and RLS policies

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types/enums
CREATE TYPE order_status_enum AS ENUM (
    'pending', 
    'confirmed', 
    'in_progress', 
    'ready', 
    'completed', 
    'canceled'
);

CREATE TYPE payment_status_enum AS ENUM (
    'pending', 
    'paid', 
    'failed', 
    'refunded'
);

-- Restaurants table
CREATE TABLE IF NOT EXISTS restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL CHECK (length(trim(name)) > 0),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(owner_id) -- One restaurant per owner for now
);

-- Menu items table
CREATE TABLE IF NOT EXISTS menu_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL CHECK (length(trim(name)) > 0),
    description TEXT,
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    category VARCHAR(100) NOT NULL CHECK (length(trim(category)) > 0),
    image_url TEXT,
    is_available BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for performance
    INDEX idx_menu_items_restaurant_id (restaurant_id),
    INDEX idx_menu_items_category (category),
    INDEX idx_menu_items_available (is_available)
);

-- Customer profiles table
CREATE TABLE IF NOT EXISTS customer_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL CHECK (length(trim(name)) > 0),
    last_order_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(restaurant_id, phone_number), -- One profile per phone per restaurant
    
    -- Indexes
    INDEX idx_customer_profiles_restaurant_phone (restaurant_id, phone_number)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    order_number VARCHAR(50) UNIQUE,
    table_number INTEGER NOT NULL CHECK (table_number > 0),
    customer_name VARCHAR(255) NOT NULL CHECK (length(trim(customer_name)) > 0),
    customer_phone VARCHAR(20) NOT NULL,
    order_status order_status_enum DEFAULT 'pending',
    payment_status payment_status_enum DEFAULT 'pending',
    payment_method VARCHAR(50) DEFAULT 'cash',
    total_price DECIMAL(10,2) NOT NULL CHECK (total_price > 0),
    estimated_time INTEGER CHECK (estimated_time > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for performance
    INDEX idx_orders_restaurant_id (restaurant_id),
    INDEX idx_orders_status (order_status),
    INDEX idx_orders_created_at (created_at),
    INDEX idx_orders_table_number (table_number)
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_order_items_order_id (order_id),
    INDEX idx_order_items_menu_item_id (menu_item_id)
);

-- Enable Row Level Security on all tables
ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

-- RLS Policies for restaurants table
CREATE POLICY "Restaurant owners can manage their own restaurant" ON restaurants
    FOR ALL USING (owner_id = auth.uid());

-- RLS Policies for menu_items table
CREATE POLICY "Restaurant owners can manage their menu items" ON menu_items
    FOR ALL USING (
        restaurant_id IN (
            SELECT id FROM restaurants WHERE owner_id = auth.uid()
        )
    );

-- Public read access for menu items (for customer menu)
CREATE POLICY "Public can read available menu items" ON menu_items
    FOR SELECT USING (is_available = true);

-- RLS Policies for customer_profiles table
CREATE POLICY "Restaurant owners can manage their customer profiles" ON customer_profiles
    FOR ALL USING (
        restaurant_id IN (
            SELECT id FROM restaurants WHERE owner_id = auth.uid()
        )
    );

-- RLS Policies for orders table
CREATE POLICY "Restaurant owners can manage their orders" ON orders
    FOR ALL USING (
        restaurant_id IN (
            SELECT id FROM restaurants WHERE owner_id = auth.uid()
        )
    );

-- Public insert access for orders (for customer ordering)
CREATE POLICY "Public can create orders" ON orders
    FOR INSERT WITH CHECK (true);

-- RLS Policies for order_items table
CREATE POLICY "Restaurant owners can manage order items for their orders" ON order_items
    FOR ALL USING (
        order_id IN (
            SELECT o.id FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE r.owner_id = auth.uid()
        )
    );

-- Public insert access for order items (for customer ordering)
CREATE POLICY "Public can create order items" ON order_items
    FOR INSERT WITH CHECK (true);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON restaurants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON menu_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customer_profiles_updated_at BEFORE UPDATE ON customer_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_order_items_updated_at BEFORE UPDATE ON order_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update customer profile last_order_at when order is created
CREATE OR REPLACE FUNCTION update_customer_last_order()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or create customer profile
    INSERT INTO customer_profiles (restaurant_id, phone_number, name, last_order_at)
    VALUES (NEW.restaurant_id, NEW.customer_phone, NEW.customer_name, NEW.created_at)
    ON CONFLICT (restaurant_id, phone_number)
    DO UPDATE SET 
        name = NEW.customer_name,
        last_order_at = NEW.created_at,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update customer profile when order is created
CREATE TRIGGER update_customer_profile_on_order AFTER INSERT ON orders
    FOR EACH ROW EXECUTE FUNCTION update_customer_last_order();