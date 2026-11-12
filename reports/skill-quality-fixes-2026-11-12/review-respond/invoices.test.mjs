import { test } from 'node:test';
import assert from 'node:assert/strict';
import { summarizeInvoices, invoiceEndpoint } from '../src/invoices.mjs';

test('summarize a nonempty v1 response', () => {
  assert.deepEqual(summarizeInvoices([{ status: 'paid' }]), { count: 1, firstStatus: 'paid' });
  assert.equal(invoiceEndpoint, '/v1/invoices');
});

test('summarize an empty success response', () => {
  assert.deepEqual(summarizeInvoices([]), { count: 0, firstStatus: null });
});
