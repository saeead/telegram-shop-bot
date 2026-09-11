# Telegram Integration

Telegram is both the user interface and product-file storage transport.

Channels:
1. Store — public, preview-only.
2. Archive — private, complete product copy.
3. Backup — private, complete product copy.

The bot receives admin-forwarded messages, groups them into an intake session, classifies media, creates a product draft, asks for metadata, then publishes after confirmation.

Never assume exactly one preview or one main file.
