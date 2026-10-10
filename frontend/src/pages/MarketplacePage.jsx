import { useEffect, useState } from 'react';
import { Package, Plus, Search, Sprout, Star } from 'lucide-react';
import { apiRequest, getSavedUser } from '../api/client.js';
import Notice from '../components/Notice.jsx';
import EmptyState from '../components/EmptyState.jsx';

const blankProduct = { name: '', category: 'fertilizer', description: '', price: '', stock_quantity: '1', unit: 'item' };
const SELLER_ROLES = ['vendor', 'farmer', 'gardener', 'nursery_manager'];

export default function MarketplacePage() {
  const user = getSavedUser();
  const canSell = SELLER_ROLES.includes(user?.role);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState(blankProduct);

  async function refreshProducts(searchTerm = '') {
    setProducts(await apiRequest(`/marketplace/products${searchTerm ? `?q=${encodeURIComponent(searchTerm)}` : ''}`));
  }

  async function refreshOrders() {
    setOrders(await apiRequest('/marketplace/orders'));
  }

  async function refreshAll(searchTerm = '') {
    setError('');
    try { await Promise.all([refreshProducts(searchTerm), refreshOrders()]); }
    catch (requestError) { setError(requestError.message); }
  }

  useEffect(() => { refreshAll(); }, []);

  async function createProduct(event) {
    event.preventDefault();
    setBusy(true); setError(''); setSuccess('');
    try {
      await apiRequest('/marketplace/products', {
        method: 'POST',
        body: JSON.stringify({ ...form, price: Number(form.price), stock_quantity: Number(form.stock_quantity) }),
      });
      setForm(blankProduct);
      setShowForm(false);
      setSuccess('Your product listing was saved.');
      await refreshProducts(query);
    } catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  }

  async function rateProduct(product) {
    const value = window.prompt('Give this product a rating from 1 to 5:');
    if (value === null) return;
    const rating = Number(value);
    if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
      setError('Enter a whole-number rating from 1 to 5.');
      return;
    }
    const comment = window.prompt('Optional short review:') || '';
    try {
      await apiRequest(`/marketplace/products/${product.id}/reviews`, { method: 'POST', body: JSON.stringify({ rating, comment }) });
      await refreshProducts(query);
      setSuccess('Your rating was saved.');
    } catch (requestError) { setError(requestError.message); }
  }

  async function placeOrder(product) {
    const quantityText = window.prompt(`Quantity to order (available: ${product.stock_quantity}):`, '1');
    if (quantityText === null) return;
    const quantity = Number(quantityText);
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > product.stock_quantity) {
      setError('Enter a whole-number quantity within the available stock.');
      return;
    }
    const deliveryAddress = window.prompt('Delivery address (include area and PIN code):');
    if (!deliveryAddress || deliveryAddress.trim().length < 8) return;
    setError(''); setSuccess('');
    try {
      await apiRequest(`/marketplace/products/${product.id}/orders`, {
        method: 'POST', body: JSON.stringify({ quantity, delivery_address: deliveryAddress.trim() }),
      });
      setSuccess('Order request saved. Stock has been updated in the database.');
      await refreshAll(query);
    } catch (requestError) { setError(requestError.message); }
  }

  async function updateOrder(order, status) {
    try {
      await apiRequest(`/marketplace/orders/${order.id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
      setSuccess(`Order #${order.id} updated to ${status.replaceAll('_', ' ')}.`);
      await refreshOrders();
    } catch (requestError) { setError(requestError.message); }
  }

  async function assignDeliveryPartner(order) {
    try {
      const partners = await apiRequest('/marketplace/delivery-partners');
      if (!partners.length) {
        setError('No active delivery-partner accounts are registered yet. Ask a teammate to create a delivery_partner account first.');
        return;
      }
      const options = partners.map((partner) => `${partner.id}: ${partner.full_name} (${partner.email})`).join('\n');
      const selected = window.prompt(`Enter the delivery-partner ID:\n${options}`, String(partners[0].id));
      if (!selected) return;
      await apiRequest(`/marketplace/orders/${order.id}`, { method: 'PATCH', body: JSON.stringify({ delivery_partner_id: Number(selected) }) });
      setSuccess('Delivery partner assigned to the order.');
      await refreshOrders();
    } catch (requestError) { setError(requestError.message); }
  }

  function searchProducts(event) {
    event.preventDefault();
    refreshProducts(query).catch((requestError) => setError(requestError.message));
  }

  return (
    <div className="page-stack">
      <div className="page-intro page-intro-row"><div><span className="eyebrow">COMMUNITY MARKETPLACE</span><h2>Care products, closer to home.</h2><p>Browse real product listings, rate products, place order requests and manage your listings if your account has seller permissions.</p></div>{canSell && <button className="button button--primary" onClick={() => setShowForm((open) => !open)}><Plus size={17} /> List a product</button>}</div>
      {error && <Notice type="error">{error}</Notice>}
      {success && <Notice type="success">{success}</Notice>}

      {showForm && <form className="panel" onSubmit={createProduct}>
        <div className="panel-heading"><div className="panel-icon tone-peach"><Package size={19} /></div><div><h3>List a product or supply</h3><p>Use clear descriptions and accurate stock details.</p></div></div>
        <div className="form-grid">
          <label>Product name *<input required minLength="2" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="e.g. Vermicompost" /></label>
          <label>Category<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}><option value="fertilizer">Fertilizer</option><option value="botanical_care">Botanical care</option><option value="soil_health">Soil health</option><option value="tools">Tools and supplies</option><option value="seeds">Seeds and seedlings</option><option value="produce">Farm produce</option></select></label>
          <label>Price (INR) *<input type="number" min="0.01" step="0.01" required value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} /></label>
          <label>Available quantity *<input type="number" min="0" step="1" required value={form.stock_quantity} onChange={(event) => setForm({ ...form, stock_quantity: event.target.value })} /></label>
          <label>Unit<input value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })} placeholder="bag, kg, bottle, tray…" /></label>
          <label className="form-full">Description *<textarea required minLength="5" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Describe the product, package size and important use or safety information." /></label>
        </div>
        <div className="form-actions"><button type="button" className="button button--secondary" onClick={() => setShowForm(false)}>Cancel</button><button className="button button--primary" disabled={busy}>{busy ? 'Saving…' : 'Publish listing'}</button></div>
      </form>}

      <section className="section-block">
        <div className="section-heading"><div><span className="eyebrow">PRODUCT CATALOGUE</span><h2>Community listings</h2></div><span className="subtle-count">{products.length} listings returned</span></div>
        <div className="toolbar"><form className="toolbar-search" onSubmit={searchProducts}><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search products" /><button aria-label="Search"><Search size={15} /></button></form><span className="subtle-count">Results are loaded from the API</span></div>
        {products.length ? <div className="product-grid">{products.map((product, index) => <article className="product-card" key={product.id}>
          <div className={`product-art product-art-${index % 4}`}><span>{product.category === 'fertilizer' ? '✳' : product.category === 'seeds' ? '❋' : '❧'}</span><small>{product.category.replaceAll('_', ' ')}</small></div>
          <div className="product-body"><div className="product-title-row"><h3>{product.name}</h3><strong>₹{Number(product.price).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</strong></div>
            <p>{product.description}</p><div className="vendor-line"><span>{product.vendor_name?.[0] || 'V'}</span><div><b>{product.vendor_name}</b><small>Community seller</small></div></div>
            <div className="product-bottom"><small><Package size={13} />{product.stock_quantity} {product.unit} available</small><button className="rating-button" onClick={() => rateProduct(product)}><Star size={15} />{product.average_rating ? `${product.average_rating} (${product.review_count})` : 'Rate'}</button></div>
            {user?.id !== product.vendor_id && <button className="button button--primary button--wide" style={{ marginTop: 12 }} disabled={product.stock_quantity < 1} onClick={() => placeOrder(product)}>{product.stock_quantity < 1 ? 'Out of stock' : 'Request an order'}</button>}
          </div>
        </article>)}</div> : <EmptyState title="The marketplace is waiting for its first listing" description={canSell ? 'Publish your first product or supply to make it visible to the community.' : 'Vendor and farmer listings will appear here once published.'} action={canSell && <button className="button button--primary" onClick={() => setShowForm(true)}><Plus size={16} /> List first product</button>} />}
      </section>

      <section className="section-block"><div className="section-heading"><div><span className="eyebrow">ORDER WORKFLOW</span><h2>{user?.role === 'vendor' || SELLER_ROLES.includes(user?.role) ? 'Orders for your listings' : user?.role === 'delivery_partner' ? 'Assigned deliveries' : 'Your orders'}</h2><p>Order records and inventory are stored in the database. Payment processing is not connected.</p></div><span className="subtle-count">{orders.length} orders</span></div>
        {orders.length ? <div className="report-list">{orders.map((order) => <article className="report-row" key={order.id}>
          <div className="report-file-icon"><Package size={19} /></div><div className="report-info"><b>{order.product_name} · {order.quantity} × ₹{Number(order.unit_price).toFixed(2)}</b><span>Order #{order.id} · Total ₹{Number(order.total).toFixed(2)} · {user?.role === 'vendor' || SELLER_ROLES.includes(user?.role) ? `Buyer: ${order.buyer_name}` : `Seller: ${order.vendor_name}`}</span><small>{order.delivery_address}</small>{order.delivery_partner_name && <small>Delivery partner: {order.delivery_partner_name}</small>}</div><span className="status-pill">{order.status.replaceAll('_', ' ')}</span>
          <div className="record-actions">{SELLER_ROLES.includes(user?.role) && order.status === 'requested' && <button title="Accept order" onClick={() => updateOrder(order, 'accepted')}>✓</button>}{SELLER_ROLES.includes(user?.role) && <button title="Assign delivery partner" onClick={() => assignDeliveryPartner(order)}>↗</button>}{user?.role === 'delivery_partner' && order.status === 'accepted' && <button title="Mark picked up" onClick={() => updateOrder(order, 'picked_up')}>1</button>}{user?.role === 'delivery_partner' && order.status === 'picked_up' && <button title="Out for delivery" onClick={() => updateOrder(order, 'out_for_delivery')}>2</button>}{user?.role === 'delivery_partner' && order.status === 'out_for_delivery' && <button title="Mark delivered" onClick={() => updateOrder(order, 'delivered')}>✓</button>}</div>
        </article>)}</div> : <EmptyState title="No orders yet" description="Order requests placed by buyers, orders for your listings, or deliveries assigned to you will appear here." />}
      </section>
      <p className="disclaimer-line"><Sprout size={14} /> TreeRasa records orders and stock changes, but does not process payments, verify certifications or connect to an external courier service.</p>
    </div>
  );
}
