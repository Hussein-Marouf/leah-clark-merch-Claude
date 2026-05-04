import express from 'express';
import cors from 'cors';
import QRCode from 'qrcode';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const DB_PATH = path.join(__dirname, 'db.json');
const CATALOG_PATH = path.join(__dirname, 'data', 'product-catalog.json');
const SCHEDULE_PATH = path.join(__dirname, 'data', 'current-schedule.json');

// Initialize lowdb
const adapter = new JSONFile(DB_PATH);
const slugifyCatalogValue = (value) => String(value || '')
  .trim()
  .toUpperCase()
  .replace(/[^A-Z0-9]+/g, '-')
  .replace(/^-|-$/g, '');

const normalizeCatalogProduct = (product, index) => {
  const price = product.price === null || product.price === undefined ? null : Number(product.price);
  const quantity = Math.max(0, Number.parseInt(product.quantity, 10) || 0);
  const image = String(product.image || product.image_url || '').trim();
  const availability = String(product.availability || '').trim().toLowerCase();
  const imageType = String(product.image_type || product.product_type || 'paper print').trim();
  const name = String(product.name || '').trim();
  const size = String(product.size || '').trim();
  const isOrderable = availability === 'available' && image && quantity > 0 && Number.isFinite(price) && price > 0;

  return {
    id: Number.isInteger(Number(product.id)) ? Number(product.id) : index + 1,
    quantity,
    image_type: imageType,
    name,
    image,
    image_url: image,
    size,
    price: Number.isFinite(price) ? price : null,
    availability: availability || (isOrderable ? 'available' : 'unavailable'),
    label: String(product.label || `${slugifyCatalogValue(imageType)}-${slugifyCatalogValue(size)}-${slugifyCatalogValue(name) || index + 1}`).trim(),
    active: product.active !== false && isOrderable
  };
};

const loadProductCatalog = async () => {
  try {
    const catalog = JSON.parse(await fs.readFile(CATALOG_PATH, 'utf8'));
    const products = Array.isArray(catalog.products)
      ? catalog.products
        .map(normalizeCatalogProduct)
        .filter((product) => product.name && product.image_type && product.size)
      : [];

    if (!products.length) {
      console.warn('Snapshot product catalog is empty or missing valid product rows.');
    }

    return products;
  } catch (err) {
    console.error('Product catalog could not be loaded:', err.message);
    return [];
  }
};

const defaultData = {
  prints: await loadProductCatalog(),
  orders: [],
  nextOrderId: 1
};

const db = new Low(adapter, defaultData);
await db.read();

const normalizeEmail = (email) => String(email || '').trim().toLowerCase();
const isValidEmail = (email) => /^\S+@\S+\.\S+$/.test(email);
const parseOrderId = (value) => {
  const id = Number.parseInt(value, 10);
  return Number.isInteger(id) && id > 0 ? id : null;
};
const isSafeHttpUrl = (value) => {
  try {
    const url = new URL(String(value || '').trim());
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
};
const orderTotals = (order) => {
  const items = Array.isArray(order.items) ? order.items : [];
  return {
    ...order,
    item_count: items.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0),
    total: items.reduce((sum, item) => sum + ((Number(item.price) || 0) * (Number(item.quantity) || 0)), 0)
  };
};

// Initialize data and keep the seeded print catalog current across deploys.
if (!db.data) {
  db.data = defaultData;
}
const currentPrints = Array.isArray(db.data.prints) ? db.data.prints : [];
const currentPrintsById = new Map(currentPrints.map((print) => [print.id, print]));
db.data.prints = defaultData.prints.map((print) => {
  const existingPrint = currentPrintsById.get(print.id);
  const sameCatalogPrint = existingPrint?.label === print.label && existingPrint?.name === print.name;
  return {
    ...print,
    active: print.active && sameCatalogPrint && typeof existingPrint.active === 'boolean' ? existingPrint.active : print.active
  };
});
db.data.orders = Array.isArray(db.data.orders)
  ? db.data.orders.filter((order) => {
    if (!order || !isValidEmail(normalizeEmail(order.email))) return false;
    order.email = normalizeEmail(order.email);
    order.items = Array.isArray(order.items) ? order.items : [];
    order.status = order.status || 'pending';
    return true;
  })
  : [];
db.data.nextOrderId = Number.isInteger(db.data.nextOrderId) && db.data.nextOrderId > 0
  ? db.data.nextOrderId
  : Math.max(0, ...db.data.orders.map((order) => Number(order.id) || 0)) + 1;

const highestExistingOrderId = Math.max(0, ...db.data.orders.map((order) => Number(order.id) || 0));
if (db.data.nextOrderId <= highestExistingOrderId) {
  db.data.nextOrderId = highestExistingOrderId + 1;
}
await db.write();

const buildOrderItems = (items) => {
  const quantityByPrintId = new Map();

  items.forEach((item) => {
    const printId = Number(item?.print_id);
    const quantity = Math.min(99, Math.max(1, Number.parseInt(item?.quantity, 10) || 1));

    if (Number.isInteger(printId)) {
      quantityByPrintId.set(printId, Math.min(99, (quantityByPrintId.get(printId) || 0) + quantity));
    }
  });

  return Array.from(quantityByPrintId.entries()).map(([printId, quantity]) => {
    const print = db.data.prints.find((candidate) => candidate.id === printId && candidate.active);
    if (!print) return null;

    return {
      print_id: print.id,
      quantity,
      name: print.name,
      label: print.label,
      size: print.size,
      image_type: print.image_type,
      price: print.price,
      image: print.image,
      image_url: print.image_url,
      availability: print.availability
    };
  }).filter(Boolean);
};

const findPendingOrderByEmail = (email) => {
  const normalizedEmail = normalizeEmail(email);
  return db.data.orders.find(
    (order) => normalizeEmail(order.email) === normalizedEmail && order.status === 'pending'
  );
};

const findPendingOrderIndexByEmail = (email) => {
  const normalizedEmail = normalizeEmail(email);
  return db.data.orders.findIndex(
    (order) => normalizeEmail(order.email) === normalizedEmail && order.status === 'pending'
  );
};

const findOrderIndexById = (id) => db.data.orders.findIndex((order) => order.id === id);

const asyncRoute = (handler) => async (req, res, next) => {
  try {
    await handler(req, res, next);
  } catch (err) {
    next(err);
  }
};

// Middleware
app.use(cors());
app.use(express.json({ limit: '100kb' }));
app.use(express.static(path.join(__dirname, 'public'), { maxAge: '0' }));
app.use('/prints', express.static(path.join(__dirname, 'prints'), { maxAge: '1h' }));
app.use('/documents', express.static(path.join(__dirname, 'documents'), { maxAge: '5m' }));

// API Routes

// Get all orderable products from the frozen snapshot
app.get('/api/prints', (req, res) => {
  const prints = db.data.prints.filter(p => p.active);
  res.json(prints);
});

app.get('/api/health', (req, res) => {
  res.json({
    ok: true,
    prints: db.data.prints.filter((print) => print.active).length,
    pending_orders: db.data.orders.filter((order) => order.status === 'pending').length
  });
});

// Get current event schedule exported from the shared Google Sheet
app.get('/api/schedule', asyncRoute(async (req, res) => {
  const schedule = JSON.parse(await fs.readFile(SCHEDULE_PATH, 'utf8'));
  res.json(schedule);
}));

// Create or update order
app.post('/api/orders', asyncRoute(async (req, res) => {
  const { email, items } = req.body;
  
  if (!email || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: 'Email and items are required' });
  }

  if (items.length > 100) {
    return res.status(400).json({ error: 'Too many items in one order' });
  }

  const normalizedEmail = normalizeEmail(email);
  if (!isValidEmail(normalizedEmail)) {
    return res.status(400).json({ error: 'A valid email is required' });
  }
  
  // Find existing pending order for this email
  const existingOrderIndex = findPendingOrderIndexByEmail(normalizedEmail);
  
  let orderId;
  const now = new Date().toISOString();
  
  // Build items with print info
  const orderItems = buildOrderItems(items);

  if (orderItems.length === 0) {
    return res.status(400).json({ error: 'At least one valid print is required' });
  }
  
  if (existingOrderIndex >= 0) {
    // Update existing order
    orderId = db.data.orders[existingOrderIndex].id;
    db.data.orders[existingOrderIndex].items = orderItems;
    db.data.orders[existingOrderIndex].updated_at = now;
  } else {
    // Create new order
    orderId = db.data.nextOrderId++;
    db.data.orders.push({
      id: orderId,
      email: normalizedEmail,
      status: 'pending',
      items: orderItems,
      created_at: now,
      updated_at: now
    });
  }
  
  await db.write();

  const savedOrder = db.data.orders.find((order) => order.id === orderId);
  
  res.json({ 
    success: true, 
    orderId,
    order: orderTotals(savedOrder),
    message: existingOrderIndex >= 0 ? 'Order updated' : 'Order created'
  });
}));

// Get order by email (customer view)
app.get('/api/orders/email/:email', (req, res) => {
  const order = findPendingOrderByEmail(req.params.email);
  
  res.json({ order: order ? orderTotals(order) : null });
});

// Admin: Get all pending orders
app.get('/api/admin/orders', (req, res) => {
  const pendingOrders = db.data.orders
    .filter(o => o.status === 'pending')
    .map(orderTotals)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  
  res.json(pendingOrders);
});

// Admin: Get specific order
app.get('/api/admin/orders/:id', (req, res) => {
  const id = parseOrderId(req.params.id);
  const order = db.data.orders.find(o => o.id === id);
  
  if (!order) {
    return res.status(404).json({ error: 'Order not found' });
  }
  
  res.json(orderTotals(order));
});

// Admin: Search by email
app.get('/api/admin/search', (req, res) => {
  const email = normalizeEmail(req.query.email);
  
  if (!email) {
    return res.status(400).json({ error: 'Email query required' });
  }
  
  const orders = db.data.orders
    .filter(o => 
      normalizeEmail(o.email).includes(email) &&
      o.status === 'pending'
    )
    .map(orderTotals)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  
  res.json(orders);
});

// Admin: Complete order
app.post('/api/admin/orders/:id/complete', asyncRoute(async (req, res) => {
  const id = parseOrderId(req.params.id);
  const orderIndex = findOrderIndexById(id);
  
  if (orderIndex < 0) {
    return res.status(404).json({ error: 'Order not found' });
  }

  db.data.orders[orderIndex].status = 'completed';
  db.data.orders[orderIndex].completed_at = new Date().toISOString();
  await db.write();

  res.json({ success: true });
}));

// Admin: Delete order
app.delete('/api/admin/orders/:id', asyncRoute(async (req, res) => {
  const id = parseOrderId(req.params.id);
  const orderIndex = findOrderIndexById(id);

  if (orderIndex < 0) {
    return res.status(404).json({ error: 'Order not found' });
  }

  db.data.orders.splice(orderIndex, 1);
  await db.write();
  
  res.json({ success: true });
}));

// Generate QR code
app.get('/api/qrcode', asyncRoute(async (req, res) => {
  const baseUrl = String(req.query.url || `${req.protocol}://${req.get('host')}`).trim();

  if (!isSafeHttpUrl(baseUrl)) {
    return res.status(400).json({ error: 'Please enter a valid http or https URL' });
  }

  const qrDataUrl = await QRCode.toDataURL(baseUrl, {
    width: 400,
    margin: 2,
    color: {
      dark: '#000000',
      light: '#ffffff'
    }
  });
  res.json({ qrcode: qrDataUrl, url: baseUrl });
}));

// Serve pages
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin.html'));
});

app.get('/qr', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'qr.html'));
});

app.get('/schedule', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'schedule.html'));
});

app.use('/api', (req, res) => {
  res.status(404).json({ error: 'API route not found' });
});

app.use((err, req, res, next) => {
  console.error(err);
  const message = req.path === '/api/schedule' ? 'Failed to load schedule' : 'Something went wrong';
  res.status(500).json({ error: message });
});

// Start server
app.listen(PORT, () => {
  console.log('');
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║           🎨 LEAH CLARK MERCH ORDER SYSTEM 🎨                 ║');
  console.log('╠══════════════════════════════════════════════════════════════╣');
  console.log(`║  Server running on port ${PORT}                                 ║`);
  console.log('║                                                              ║');
  console.log(`║  📱 Customer Page:  http://localhost:${PORT}                    ║`);
  console.log(`║  📋 Admin Panel:    http://localhost:${PORT}/admin              ║`);
  console.log(`║  🔲 QR Code Page:   http://localhost:${PORT}/qr                 ║`);
  console.log(`║  🗓️  Schedule Page:  http://localhost:${PORT}/schedule           ║`);
  console.log('║                                                              ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log('');
});
