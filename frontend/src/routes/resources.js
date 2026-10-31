const product = { type: 'remote', endpoint: '/products/' }
const plan = { type: 'remote', endpoint: '/plans/' }
const customer = { type: 'remote', endpoint: '/customers/' }
const term = { type: 'remote', endpoint: '/payment-terms/' }

export const resources = {
  customers: {
    title: 'Customers', singular: 'Customer', endpoint: '/customers/', writeRoles: ['admin', 'staff'],
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'company', label: 'Company' },
      { key: 'email', label: 'Email' },
      { key: 'assigned_to_email', label: 'Assigned to', sortable: false },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'email', label: 'Email', type: 'email', required: true },
      { name: 'company', label: 'Company' },
      { name: 'phone', label: 'Phone' },
      { name: 'gst_number', label: 'GST number' },
      { name: 'assigned_to', label: 'Assigned to', ...{ type: 'remote', endpoint: '/users/', optionLabel: (user) => user.email } },
      { name: 'billing_address', label: 'Billing address', type: 'textarea' },
    ],
  },
  staff: {
    title: 'Staff', singular: 'Staff member', endpoint: '/users/',
    columns: [
      { key: 'email', label: 'Email' },
      { key: 'first_name', label: 'First name' },
      { key: 'last_name', label: 'Last name' },
      { key: 'role', label: 'Role', sortable: false },
    ],
    fields: [
      { name: 'email', label: 'Email', type: 'email', required: true },
      { name: 'first_name', label: 'First name' },
      { name: 'last_name', label: 'Last name' },
      { name: 'password', label: 'Temporary password', type: 'password', hint: 'More than 8 characters, with upper case, lower case and a special character.' },
    ],
  },
  products: {
    title: 'Products', singular: 'Product', endpoint: '/products/', canDelete: true, defaults: { status: 'active', product_type: 'software' },
    filters: [{ name: 'status', label: 'Status', options: ['active', 'archived'] }],
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'product_type', label: 'Type' },
      { key: 'sales_price', label: 'Sales price', type: 'money' },
      { key: 'cost_price', label: 'Cost price', type: 'money' },
      { key: 'status', label: 'Status', type: 'status' },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'product_type', label: 'Type', type: 'select', options: ['software', 'add_on', 'service'], required: true },
      { name: 'sales_price', label: 'Sales price', type: 'number', required: true },
      { name: 'cost_price', label: 'Cost price', type: 'number', required: true },
      { name: 'status', label: 'Status', type: 'select', options: ['active', 'archived'] },
      { name: 'notes', label: 'Notes', type: 'textarea' },
    ],
  },
  variants: {
    title: 'Product variants', singular: 'Variant', endpoint: '/variants/', canDelete: true,
    columns: [
      { key: 'product_name', label: 'Product', sortable: false },
      { key: 'name', label: 'Variant' },
      { key: 'extra_price', label: 'Extra price', type: 'money' },
    ],
    fields: [
      { name: 'product', label: 'Product', required: true, ...product },
      { name: 'name', label: 'Variant name', required: true },
      { name: 'extra_price', label: 'Extra price', type: 'number', required: true },
    ],
  },
  plans: {
    title: 'Plans', singular: 'Plan', endpoint: '/plans/', canDelete: true,
    defaults: { interval: 'monthly', min_quantity: 1, status: 'active', can_close_early: true, can_pause: true, can_renew: true },
    filters: [
      { name: 'interval', label: 'Billing', options: ['daily', 'weekly', 'monthly', 'yearly'] },
      { name: 'status', label: 'Status', options: ['active', 'inactive'] },
    ],
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'product_name', label: 'Product', sortable: false },
      { key: 'price', label: 'Price', type: 'money' },
      { key: 'interval', label: 'Billing' },
      { key: 'min_quantity', label: 'Min. quantity' },
      { key: 'status', label: 'Status', type: 'status' },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'product', label: 'Product', required: true, ...product },
      { name: 'price', label: 'Price', type: 'number', required: true },
      { name: 'interval', label: 'Billing interval', type: 'select', options: ['daily', 'weekly', 'monthly', 'yearly'], required: true },
      { name: 'min_quantity', label: 'Minimum quantity', type: 'number', required: true },
      { name: 'status', label: 'Status', type: 'select', options: ['active', 'inactive'] },
      { name: 'available_from', label: 'Available from', type: 'date', required: true },
      { name: 'available_to', label: 'Available until', type: 'date' },
      { name: 'auto_close', label: 'Close automatically at expiry', type: 'checkbox' },
      { name: 'can_close_early', label: 'Can be closed early', type: 'checkbox' },
      { name: 'can_pause', label: 'Can be paused', type: 'checkbox' },
      { name: 'can_renew', label: 'Can be renewed', type: 'checkbox' },
    ],
  },
  paymentTerms: {
    title: 'Payment terms', singular: 'Payment term', endpoint: '/payment-terms/', canDelete: true,
    columns: [{ key: 'name', label: 'Name' }, { key: 'days', label: 'Days to pay' }],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'days', label: 'Days to pay', type: 'number', required: true },
    ],
  },
  taxes: {
    title: 'Taxes', singular: 'Tax', endpoint: '/taxes/', canDelete: true, defaults: { kind: 'percent', active: true, applies_to_all: true },
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'kind', label: 'Method' },
      { key: 'rate', label: 'Rate' },
      { key: 'active', label: 'Active', type: 'bool' },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'kind', label: 'Method', type: 'select', options: ['percent', 'fixed'], required: true },
      { name: 'rate', label: 'Rate or amount', type: 'number', required: true },
      { name: 'active', label: 'Active', type: 'checkbox' },
      { name: 'applies_to_all', label: 'Applies to all products', type: 'checkbox' },
      { name: 'products', label: 'Or only these products', multiple: true, ...product },
      { name: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  discounts: {
    title: 'Discounts', singular: 'Discount', endpoint: '/discounts/', canDelete: true, defaults: { kind: 'percent', scope: 'subscription', active: true },
    filters: [{ name: 'kind', label: 'Type', options: ['percent', 'fixed'] }],
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'kind', label: 'Type' },
      { key: 'value', label: 'Value' },
      { key: 'scope', label: 'Applies to' },
      { key: 'ends_on', label: 'Ends', type: 'date' },
      { key: 'times_used', label: 'Used' },
      { key: 'usage_limit', label: 'Limit' },
      { key: 'active', label: 'Active', type: 'bool' },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'kind', label: 'Type', type: 'select', options: ['percent', 'fixed'], required: true },
      { name: 'value', label: 'Value', type: 'number', required: true },
      { name: 'scope', label: 'Applies to', type: 'select', options: ['subscription', 'product'], required: true },
      { name: 'min_purchase', label: 'Minimum purchase', type: 'number' },
      { name: 'min_quantity', label: 'Minimum quantity', type: 'number' },
      { name: 'starts_on', label: 'Starts', type: 'date', required: true },
      { name: 'ends_on', label: 'Ends', type: 'date' },
      { name: 'usage_limit', label: 'Usage limit', type: 'number' },
      { name: 'active', label: 'Active', type: 'checkbox' },
      { name: 'products', label: 'Products', multiple: true, hint: 'Used when it applies to products.', ...product },
    ],
  },
  quotationTemplates: {
    title: 'Quotation templates', singular: 'Template', endpoint: '/quotation-templates/', canDelete: true,
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'plan_name', label: 'Plan', sortable: false },
      { key: 'validity_days', label: 'Valid for (days)' },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'plan', label: 'Plan', required: true, ...plan },
      { name: 'validity_days', label: 'Valid for (days)', type: 'number', required: true },
      { name: 'payment_term', label: 'Payment terms', ...term },
    ],
  },
  auditLogs: {
    title: 'Audit log', singular: 'Entry', endpoint: '/audit-logs/',
    columns: [
      { key: 'created_at', label: 'When', type: 'date' },
      { key: 'user_email', label: 'User', sortable: false },
      { key: 'action', label: 'Action' },
      { key: 'model', label: 'Record' },
      { key: 'object_id', label: 'ID' },
    ],
  },
}

export const fieldRefs = { customer, plan, product, term }
