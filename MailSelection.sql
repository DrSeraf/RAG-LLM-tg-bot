SELECT e.email, m.user_message, m.bot_response, created_at
FROM boriy_bot.emails e
JOIN boriy_bot.messages m ON e.user_id = m.user_id
WHERE m.user_id = 349724724;  -- Замените 349724724 на нужный user_id