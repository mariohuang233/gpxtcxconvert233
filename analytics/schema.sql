-- Only counters and hashed random browser identifiers; no tracks, filenames or IPs.
CREATE TABLE IF NOT EXISTS total_counts (event TEXT PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS daily_counts (day TEXT NOT NULL, event TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(day,event));
CREATE TABLE IF NOT EXISTS visitors (visitor_hash TEXT PRIMARY KEY, first_day TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS daily_visitors (day TEXT NOT NULL, visitor_hash TEXT NOT NULL, PRIMARY KEY(day,visitor_hash));
CREATE TABLE IF NOT EXISTS received_events (event_id TEXT PRIMARY KEY, day TEXT NOT NULL, event TEXT NOT NULL, visitor_hash TEXT, received_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS received_events_age ON received_events(received_at);
CREATE TRIGGER IF NOT EXISTS new_visitor AFTER INSERT ON visitors BEGIN
  INSERT INTO total_counts VALUES ('unique_visitors',1) ON CONFLICT(event) DO UPDATE SET count=count+1;
END;
CREATE TRIGGER IF NOT EXISTS new_daily_visitor AFTER INSERT ON daily_visitors BEGIN
  INSERT INTO daily_counts VALUES (NEW.day,'unique_visitors',1) ON CONFLICT(day,event) DO UPDATE SET count=count+1;
END;
CREATE TRIGGER IF NOT EXISTS new_event AFTER INSERT ON received_events BEGIN
  INSERT INTO total_counts VALUES (NEW.event,1) ON CONFLICT(event) DO UPDATE SET count=count+1;
  INSERT INTO daily_counts VALUES (NEW.day,NEW.event,1) ON CONFLICT(day,event) DO UPDATE SET count=count+1;
  INSERT OR IGNORE INTO visitors SELECT NEW.visitor_hash,NEW.day WHERE NEW.event='page_view' AND NEW.visitor_hash IS NOT NULL;
  INSERT OR IGNORE INTO daily_visitors SELECT NEW.day,NEW.visitor_hash WHERE NEW.event='page_view' AND NEW.visitor_hash IS NOT NULL;
END;
