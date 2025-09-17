-- Migration: Add order confirmation fields
-- This migration adds order_number, payment_method, and estimated_time fields to the orders table

-- Add new columns to orders table
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS order_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'cash',
ADD COLUMN IF NOT EXISTS estimated_time INTEGER CHECK (estimated_time > 0);

-- Create unique index on order_number (allowing nulls for existing records)
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_order_number ON orders (order_number) WHERE order_number IS NOT NULL;

-- Update existing orders to have order numbers (optional - can be done gradually)
-- This is commented out to avoid conflicts with existing data
-- UPDATE orders SET order_number = 'ORD-' || EXTRACT(EPOCH FROM created_at)::text || '-' || SUBSTRING(id::text, 1, 3) WHERE order_number IS NULL;