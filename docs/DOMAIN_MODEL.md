# Domain Model

## Product
- id
- product_code
- name
- category
- tags
- price
- currency
- status
- description
- created_by
- created_at / updated_at

## ProductFile
- id
- product_id
- role: preview | main
- media_type
- original_filename
- extension
- telegram_chat_id
- telegram_message_id
- telegram_file_id (when available)
- ordering
- checksum metadata if available without downloading/persisting file bytes

## Order
- id
- order_code
- customer_id
- product_id
- amount
- currency
- status
- created_at / paid_at / fulfilled_at

## Payment
- id
- order_id
- provider
- provider_reference
- status
- amount
- raw-safe metadata
- idempotency key
- timestamps

## AuditLog
Records actor, action, target, before/after-safe metadata, timestamp, and correlation ID. Never log secrets or payment credentials.
