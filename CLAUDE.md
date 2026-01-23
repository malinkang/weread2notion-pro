# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WeRead2Notion-Pro is a Python application that syncs WeChat Reading (微信读书) data to Notion. It automatically synchronizes books, highlights, notes, reading progress, and reading time statistics via GitHub Actions.

The system creates and maintains multiple Notion databases: books (书架), bookmarks (划线), reviews (笔记), chapters (章节), reading records (阅读记录), authors (作者), categories (分类), and time-based databases (日/周/月/年).

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Running Sync Commands

The package provides three main console scripts:

```bash
# Sync books from WeRead to Notion
python -m weread2notionpro.book

# Sync highlights and notes
python -m weread2notionpro.weread

# Sync reading time and update heatmap
python -m weread2notionpro.read_time
```

Alternatively, use the installed console scripts:
```bash
book
weread
read_time
```

## Architecture

### Core Components

**weread_api.py**: WeChat Reading API client
- Handles authentication via cookies (direct or CookieCloud)
- Implements session management with homepage visits to maintain valid sessions
- All API methods decorated with `@retry` for resilience
- Key methods: `get_bookshelf()`, `get_entire_shelf()`, `get_notebooklist()`, `get_bookmark_list()`, `get_chapter_info()`, `get_read_info()`
- **Local Books Support**: `get_entire_shelf()` retrieves all books including locally uploaded ones (bookId starts with `CB_`)

**notion_helper.py**: Notion API wrapper
- Manages multiple inter-related Notion databases
- Automatic database discovery via `search_database()` - recursively finds child databases
- Implements relation management for temporal databases (日/周/月/年)
- Uses caching (`__cache`) to avoid duplicate relation lookups
- Auto-creates missing databases (阅读记录, 设置) on initialization
- Settings database allows remote configuration of sync behavior (block style, color settings, bookmark sync)

**book.py**: Book synchronization logic
- Syncs book metadata, reading progress, and daily reading records
- Smart sync: skips books that haven't changed using multi-criteria comparison (readingTime, category, cover, rating)
- Handles missing data gracefully (bookProgress, archive can be None)
- Creates nested reading record entries linked to books
- **Local Books Support**: Uses `get_entire_shelf()` to retrieve all books including locally uploaded ones
  - Caches book metadata from `entire_shelf` for local books (which can't be fetched via `get_bookinfo()`)
  - Handles missing fields (author, readingTime, etc.) with default values
  - Local books identified by bookId prefix `CB_`

**weread.py**: Highlights and notes synchronization
- Syncs bookmarks (划线) and reviews (笔记/想法) with deduplication
- Manages chapter structure and note ordering via `sort_notes()`
- Batch processing: appends up to 100 blocks at a time to avoid Notion API limits
- Tracks block IDs to enable incremental updates and deletion of removed content
- Adds table of contents automatically to book pages

**read_time.py**: Reading time tracking and heatmap generation
- Syncs daily reading duration data
- Updates embedded heatmap visualization from generated SVG in OUT_FOLDER
- Handles UTC+8 timezone conversion for Chinese users

### Data Flow

1. **Authentication**: WeReadApi initializes with cookie (from env or CookieCloud)
2. **Discovery**: NotionHelper discovers existing Notion database structure
3. **Sync Books**: Fetch bookshelf → compare with Notion → update/create book pages → sync daily reading records
4. **Sync Notes**: Fetch notebook list → get bookmarks/reviews → organize by chapters → append/update blocks
5. **Sync Time**: Fetch reading time data → generate heatmap → update daily database and heatmap embed

### Key Architectural Patterns

**Incremental Sync**: The system tracks `blockId` for bookmarks, reviews, and chapters to enable updates and deletions. The `Sort` property on books indicates the last sync state.

**Relation Networks**: Books relate to authors, categories, and temporal databases (日/周/月/年). Reading records relate back to books. This creates a rich interconnected data model in Notion.

**Graceful Degradation**: API calls handle missing data (None checks), expired cookies (errcode -2012, -2010), and partial responses. The system continues processing even if individual books fail.

**Block Management**: Due to Notion's 100-block append limit, `weread.py` implements batch processing with `append_blocks_to_notion()`, tracking position via `before_block_id`.

## Environment Variables

Required:
- `NOTION_TOKEN`: Notion integration token
- `NOTION_PAGE`: Notion page URL/ID containing databases
- `WEREAD_COOKIE`: WeChat Reading cookie (or use CookieCloud)

Optional CookieCloud:
- `CC_URL`: CookieCloud server URL (default: https://cc.chenge.ink)
- `CC_ID`: CookieCloud ID
- `CC_PASSWORD`: CookieCloud password

Optional database name overrides:
- `BOOK_DATABASE_NAME`, `REVIEW_DATABASE_NAME`, `BOOKMARK_DATABASE_NAME`, etc.

## Common Debugging Scenarios

**Cookie Expiration**: Error codes -2012 or -2010 indicate expired WeChat Reading cookies. The system will print a guide URL.

**Chapter Info API**: `get_chapter_info()` has complex retry logic and supports multiple response formats due to API inconsistency. It includes delays and proper headers to avoid rate limiting.

**Missing Database**: If temporal databases (日/周/月/年) don't exist, they're created on first use via `get_*_relation_id()` methods.

**Local Books**: Books uploaded locally to WeRead (bookId starts with `CB_`) may have limited metadata available through the API. The system caches metadata from `get_entire_shelf()` and uses default values for missing fields (e.g., "未知作者" for author).
