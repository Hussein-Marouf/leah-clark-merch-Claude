import express from 'express';
import cors from 'cors';
import QRCode from 'qrcode';
import path from 'path';
import { fileURLToPath } from 'url';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize lowdb
const adapter = new JSONFile(path.join(__dirname, 'db.json'));
const defaultData = {
  prints: [
    { id: 1, name: 'Aria - The Chariot', label: 'ARIA-CHARIOT', size: '8.5x11', price: 15.00, image_url: '/prints/Aria_Chariot.png', active: true },
    { id: 2, name: 'Aria - The Chariot', label: 'ARIA-CHARIOT-LG', size: '11x17', price: 25.00, image_url: '/prints/Aria_Chariot.png', active: true },
    { id: 3, name: 'Asia Argento', label: 'ASIA-ARGENTO', size: '8.5x11', price: 15.00, image_url: '/prints/asia1-85x11.png', active: true },
    { id: 4, name: 'Asia Argento', label: 'ASIA-ARGENTO-LG', size: '11x17', price: 25.00, image_url: '/prints/asia1-85x11.png', active: true },
    { id: 5, name: 'Himiko Toga - Red', label: 'TOGA-RED', size: '8.5x11', price: 15.00, image_url: '/prints/Cute_Red_Toga_11x17_tall.png', active: true },
    { id: 6, name: 'Himiko Toga - Red', label: 'TOGA-RED-LG', size: '11x17', price: 25.00, image_url: '/prints/Cute_Red_Toga_11x17_tall.png', active: true },
    { id: 7, name: 'Himiko Toga - Mask', label: 'TOGA-MASK', size: '8.5x11', price: 15.00, image_url: '/prints/Himiko_Toga__Mask_2.jpg', active: true },
    { id: 8, name: 'Himiko Toga - Mask', label: 'TOGA-MASK-LG', size: '11x17', price: 25.00, image_url: '/prints/Himiko_Toga__Mask_2.jpg', active: true },
    { id: 9, name: "Leah's Art", label: 'LEAHS-ART', size: '8.5x11', price: 15.00, image_url: '/prints/Leahs_Art.jpg', active: true },
    { id: 10, name: "Leah's Art", label: 'LEAHS-ART-LG', size: '11x17', price: 25.00, image_url: '/prints/Leahs_Art.jpg', active: true },
    { id: 11, name: 'Through The Key Hole', label: 'KEY-HOLE', size: '8.5x11', price: 15.00, image_url: '/prints/Through_The_Key_Hole.jpg', active: true },
    { id: 12, name: 'Through The Key Hole', label: 'KEY-HOLE-LG', size: '11x17', price: 25.00, image_url: '/prints/Through_The_Key_Hole.jpg', active: true },
    { id: 13, name: 'Toga Chaco Daylen', label: 'TOGA-CHACO-DAYLEN', size: '8.5x11', price: 15.00, image_url: '/prints/Toga_Chaco_Daylen.jpg', active: true },
    { id: 14, name: 'Toga Chaco Daylen', label: 'TOGA-CHACO-DAYLEN-LG', size: '11x17', price: 25.00, image_url: '/prints/Toga_Chaco_Daylen.jpg', active: true },
  ],
  orders: [],
  nextOrderId: 1
};

const db = new Low(adapter, defaultData);
await db.read();

// Initialize default data if empty or null
if (!db.data) {
  db.data = defaultData;
}
if (!db.data.prints || db.data.prints.length === 0) {
  db.data.prints = defaultData.prints;
}
const existingPrintIds = new Set(db.data.prints.map((print) => print.id));
defaultData.prints.forEach((print) => {
  if (!existingPrintIds.has(print.id)) {
    db.data.prints.push(print);
  }
});
db.data.orders = Array.isArray(db.data.orders) ? db.data.orders : [];
db.data.nextOrderId = Number.isInteger(db.data.nextOrderId) ? db.data.nextOrderId : 1;
await db.write();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/prints', express.static(path.join(__dirname, 'prints')));

// API Routes

// Get all active prints
app.get('/api/prints', (req, res) => {
  const prints = db.data.prints.filter(p => p.active);
  res.json(prints);
});

// Create or update order
app.post('/api/orders', async (req, res) => {
  const { email, items } = req.body;
  
  if (!email || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: 'Email and items are required' });
  }

  const normalizedEmail = String(email).trim().toLowerCase();
  if (!/^\S+@\S+\.\S+$/.test(normalizedEmail)) {
    return res.status(400).json({ error: 'A valid email is required' });
  }
  
  // Find existing pending order for this email
  const existingOrderIndex = db.data.orders.findIndex(
    o => o.email.toLowerCase() === normalizedEmail && o.status === 'pending'
  );
  
  let orderId;
  const now = new Date().toISOString();
  
  // Build items with print info
  const orderItems = items.map(item => {
    const printId = Number(item.print_id);
    const print = db.data.prints.find(p => p.id === printId && p.active);
    if (!print) return null;

    const quantity = Math.max(1, Number.parseInt(item.quantity, 10) || 1);
    return {
      print_id: print.id,
      quantity,
      name: print.name,
      label: print.label,
      size: print.size,
      price: print.price,
      image_url: print.image_url
    };
  }).filter(Boolean);

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
  
  res.json({ 
    success: true, 
    orderId,
    message: existingOrderIndex >= 0 ? 'Order updated' : 'Order created'
  });
});

// Get order by email (customer view)
app.get('/api/orders/email/:email', (req, res) => {
  const { email } = req.params;
  
  const order = db.data.orders.find(
    o => o.email.toLowerCase() === email.toLowerCase() && o.status === 'pending'
  );
  
  res.json({ order: order || null });
});

// Admin: Get all pending orders
app.get('/api/admin/orders', (req, res) => {
  const pendingOrders = db.data.orders
    .filter(o => o.status === 'pending')
    .map(order => ({
      ...order,
      item_count: order.items.reduce((sum, i) => sum + i.quantity, 0),
      total: order.items.reduce((sum, i) => sum + (i.price * i.quantity), 0)
    }))
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  
  res.json(pendingOrders);
});

// Admin: Get specific order
app.get('/api/admin/orders/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const order = db.data.orders.find(o => o.id === id);
  
  if (!order) {
    return res.status(404).json({ error: 'Order not found' });
  }
  
  res.json(order);
});

// Admin: Search by email
app.get('/api/admin/search', (req, res) => {
  const { email } = req.query;
  
  if (!email) {
    return res.status(400).json({ error: 'Email query required' });
  }
  
  const orders = db.data.orders
    .filter(o => 
      o.email.toLowerCase().includes(email.toLowerCase()) && 
      o.status === 'pending'
    )
    .map(order => ({
      ...order,
      item_count: order.items.reduce((sum, i) => sum + i.quantity, 0),
      total: order.items.reduce((sum, i) => sum + (i.price * i.quantity), 0)
    }))
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  
  res.json(orders);
});

// Admin: Complete order
app.post('/api/admin/orders/:id/complete', async (req, res) => {
  const id = parseInt(req.params.id);
  const orderIndex = db.data.orders.findIndex(o => o.id === id);
  
  if (orderIndex >= 0) {
    db.data.orders[orderIndex].status = 'completed';
    db.data.orders[orderIndex].completed_at = new Date().toISOString();
    await db.write();
  }
  
  res.json({ success: true });
});

// Admin: Delete order
app.delete('/api/admin/orders/:id', async (req, res) => {
  const id = parseInt(req.params.id);
  db.data.orders = db.data.orders.filter(o => o.id !== id);
  await db.write();
  
  res.json({ success: true });
});

// Generate QR code
app.get('/api/qrcode', async (req, res) => {
  const baseUrl = req.query.url || `${req.protocol}://${req.get('host')}`;
  
  try {
    const qrDataUrl = await QRCode.toDataURL(baseUrl, {
      width: 400,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#ffffff'
      }
    });
    res.json({ qrcode: qrDataUrl, url: baseUrl });
  } catch (err) {
    res.status(500).json({ error: 'Failed to generate QR code' });
  }
});

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
  console.log('║                                                              ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log('');
});
