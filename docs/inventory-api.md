# Inventory Management API Documentation

## Overview

The inventory management system provides comprehensive APIs for tracking product inventory across stores, managing stock movements, and monitoring inventory levels. The system enforces brand-based access control and role-based permissions.

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Permissions

### Role-based Access:
- **SYSTEM_ADMIN**: Full access to all inventory data across brands
- **BRAND_MANAGER**: Full access to their brand's inventory data  
- **STORE_MANAGER**: Read and update access to their brand's inventory
- **STAFF**: Read-only access to their brand's inventory

### Brand Scoping:
Non-admin users can only access inventory data for their assigned brand.

## Models

### ProductStore

Represents inventory of a specific product at a specific store.

**Fields:**
- `id` (UUID): Unique identifier
- `product` (UUID): Reference to Product
- `store` (UUID): Reference to Store  
- `quantity_on_hand` (integer): Current physical stock quantity
- `reserved_quantity` (integer): Quantity reserved for orders
- `minimum_stock_level` (integer): Minimum level for reorder alerts
- `available_quantity` (computed): quantity_on_hand - reserved_quantity
- `is_below_minimum` (computed): true if quantity_on_hand < minimum_stock_level

**Constraints:**
- Product and Store must belong to the same brand
- Reserved quantity cannot exceed quantity on hand
- Unique together: (product, store)

### StockMovement

Tracks all inventory movements and changes.

**Fields:**
- `id` (UUID): Unique identifier
- `product_store` (UUID): Reference to ProductStore
- `movement_type` (choice): INBOUND, OUTBOUND, TRANSFER, ADJUSTMENT
- `quantity` (integer): Change amount (positive for increases, negative for decreases)
- `reference_number` (string): External reference (PO, SO, etc.)
- `notes` (text): Additional details
- `created_by` (UUID): User who created the movement
- `destination_product_store` (UUID): For transfers, the destination ProductStore
- `created_at` (datetime): When the movement was created

**Business Rules:**
- INBOUND movements must have positive quantity
- OUTBOUND movements must have negative quantity  
- TRANSFER movements require a destination_product_store
- Stock movements automatically update ProductStore quantities
- Movements are immutable after creation (no updates allowed)

## API Endpoints

### ProductStore Endpoints

#### List Product Stores
```
GET /api/product-stores/
```

**Query Parameters:**
- `product`: Filter by product ID
- `store`: Filter by store ID
- `product__brand`: Filter by brand ID
- `search`: Search product name, SKU, store name, or code
- `ordering`: Order by quantity_on_hand, reserved_quantity, minimum_stock_level, created_at

**Response:** Paginated list of ProductStore objects

#### Create Product Store
```
POST /api/product-stores/
```

**Permissions:** BRAND_MANAGER, SYSTEM_ADMIN

**Request Body:**
```json
{
    "product": "uuid",
    "store": "uuid", 
    "quantity_on_hand": 100,
    "reserved_quantity": 10,
    "minimum_stock_level": 5
}
```

#### Retrieve Product Store
```
GET /api/product-stores/{id}/
```

**Response:** Detailed ProductStore with nested product and store information

#### Update Product Store
```
PUT/PATCH /api/product-stores/{id}/
```

**Permissions:** BRAND_MANAGER, STORE_MANAGER, SYSTEM_ADMIN

#### Delete Product Store
```
DELETE /api/product-stores/{id}/
```

**Permissions:** BRAND_MANAGER, SYSTEM_ADMIN

#### Low Stock Alert
```
GET /api/product-stores/low_stock/
```

Returns products where quantity_on_hand < minimum_stock_level

### StockMovement Endpoints

#### List Stock Movements
```
GET /api/stock-movements/
```

**Query Parameters:**
- `product_store`: Filter by ProductStore ID
- `movement_type`: Filter by movement type
- `created_by`: Filter by user ID
- `search`: Search product name, SKU, store name, reference number, or notes
- `ordering`: Order by quantity, created_at

**Response:** Paginated list of StockMovement objects

#### Create Stock Movement
```
POST /api/stock-movements/
```

**Request Body:**
```json
{
    "product_store": "uuid",
    "movement_type": "INBOUND",
    "quantity": 50,
    "reference_number": "PO001",
    "notes": "Initial stock receipt"
}
```

For transfers, also include:
```json
{
    "destination_product_store": "uuid"
}
```

**Automatic Actions:**
- Updates ProductStore quantity_on_hand
- Sets created_by to authenticated user
- For transfers, updates both source and destination quantities

#### Retrieve Stock Movement
```
GET /api/stock-movements/{id}/
```

**Response:** Detailed StockMovement with nested ProductStore information

#### Delete Stock Movement
```
DELETE /api/stock-movements/{id}/
```

**Permissions:** SYSTEM_ADMIN only (for data integrity)

**Note:** Stock movements cannot be updated (PUT/PATCH not allowed)

#### Filter by Product
```
GET /api/stock-movements/by_product/?product_id={uuid}
```

Returns all movements for a specific product across all stores.

#### Filter by Store
```
GET /api/stock-movements/by_store/?store_id={uuid}
```

Returns all movements for a specific store across all products.

## Example Workflows

### 1. Receive New Inventory

```bash
# Create inbound movement
curl -X POST /api/stock-movements/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_store": "product-store-uuid",
    "movement_type": "INBOUND", 
    "quantity": 100,
    "reference_number": "PO2024001",
    "notes": "Weekly inventory delivery"
  }'
```

### 2. Process Sale/Order

```bash
# Create outbound movement  
curl -X POST /api/stock-movements/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_store": "product-store-uuid",
    "movement_type": "OUTBOUND",
    "quantity": -5,
    "reference_number": "SO2024001", 
    "notes": "Customer order fulfillment"
  }'
```

### 3. Transfer Between Stores

```bash
# Create transfer movement
curl -X POST /api/stock-movements/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_store": "source-store-uuid",
    "movement_type": "TRANSFER",
    "quantity": -20,
    "destination_product_store": "destination-store-uuid",
    "reference_number": "TR2024001",
    "notes": "Stock rebalancing"
  }'
```

### 4. Check Low Stock

```bash
# Get products below minimum stock
curl /api/product-stores/low_stock/ \
  -H "Authorization: Bearer <token>"
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `405 Method Not Allowed`: HTTP method not supported

Error response format:
```json
{
    "detail": "Error message",
    "code": "ERROR_CODE"
}
```

## Data Validation

### ProductStore Validation
- Product and store must belong to same brand
- Reserved quantity ≤ quantity on hand
- All quantities must be non-negative

### StockMovement Validation
- INBOUND movements: quantity > 0
- OUTBOUND movements: quantity < 0  
- TRANSFER movements: require destination_product_store
- Cannot create movements causing negative stock (except ADJUSTMENT)
- User must have access to product's brand

## Rate Limiting

API requests may be rate limited. Check response headers:
- `X-RateLimit-Limit`: Request limit per time window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets