export const invoiceEndpoint = '/v1/invoices';

export function summarizeInvoices(items) {
  return { count: items.length, firstStatus: items[0].status };
}
