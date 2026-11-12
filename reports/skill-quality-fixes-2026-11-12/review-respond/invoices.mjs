export const invoiceEndpoint = '/v1/invoices';

export function summarizeInvoices(items) {
  return { count: items.length, firstStatus: items.length === 0 ? null : items[0].status };
}
