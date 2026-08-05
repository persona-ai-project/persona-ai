"""
test_parsers.py
===============
Unit tests for all 5 parsers.
Each test uses minimal 3-line sample input.

Run:
    cd services/ai
    python -m pytest tests/test_parsers.py -v
"""
from __future__ import annotations

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.contracts.chunk import Chunk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from parsers.whatsapp import parse_whatsapp
from parsers.markdown import parse_markdown
from parsers.text import parse_text


class TestWhatsAppParser:

    def test_basic_parse(self, tmp_path):
        chat = tmp_path / "chat.txt"
        chat.write_text(
            "1/1/24, 10:00 - Alice: Hello there\n"
            "1/1/24, 10:01 - Bob: Hi Alice!\n"
            "1/1/24, 10:02 - Alice: How are you?\n",
            encoding="utf-8"
        )
        chunks = parse_whatsapp(str(chat), owner_name="Alice")
        assert len(chunks) == 2
        assert all(c.source == "whatsapp" for c in chunks)
        assert chunks[0].text == "Hello there"
        assert chunks[1].text == "How are you?"

    def test_multiline_message(self, tmp_path):
        chat = tmp_path / "chat.txt"
        chat.write_text(
            "1/1/24, 10:00 - Alice: First line\n"
            "second line\n"
            "third line\n",
            encoding="utf-8"
        )
        chunks = parse_whatsapp(str(chat), owner_name="Alice")
        assert len(chunks) == 1
        assert "First line" in chunks[0].text
        assert "second line" in chunks[0].text

    def test_system_messages_skipped(self, tmp_path):
        chat = tmp_path / "chat.txt"
        chat.write_text(
            "1/1/24, 10:00 - Alice: Messages and calls are end-to-end encrypted\n"
            "1/1/24, 10:01 - Alice: Hello\n",
            encoding="utf-8"
        )
        chunks = parse_whatsapp(str(chat), owner_name="Alice")
        assert len(chunks) == 1
        assert chunks[0].text == "Hello"

    def test_returns_chunk_objects(self, tmp_path):
        chat = tmp_path / "chat.txt"
        chat.write_text(
            "1/1/24, 10:00 - Alice: Test message\n",
            encoding="utf-8"
        )
        chunks = parse_whatsapp(str(chat), owner_name="Alice")
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_wrong_owner_returns_empty(self, tmp_path):
        chat = tmp_path / "chat.txt"
        chat.write_text(
            "1/1/24, 10:00 - Bob: Hello\n",
            encoding="utf-8"
        )
        chunks = parse_whatsapp(str(chat), owner_name="Alice")
        assert chunks == []

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_whatsapp("nonexistent.txt", owner_name="Alice")


class TestMarkdownParser:

    def test_basic_parse(self, tmp_path):
        md = tmp_path / "notes.md"
        md.write_text(
            "# Title\n"
            "Some content here.\n"
            "More content.\n",
            encoding="utf-8"
        )
        chunks = parse_markdown(str(md))
        assert len(chunks) == 1
        assert chunks[0].source == "markdown"
        assert "Title" in chunks[0].text

    def test_empty_file_returns_empty(self, tmp_path):
        md = tmp_path / "empty.md"
        md.write_text("", encoding="utf-8")
        chunks = parse_markdown(str(md))
        assert chunks == []

    def test_returns_chunk_object(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("Hello world", encoding="utf-8")
        chunks = parse_markdown(str(md))
        assert isinstance(chunks[0], Chunk)

    def test_source_id_defaults_to_filename(self, tmp_path):
        md = tmp_path / "myfile.md"
        md.write_text("Content", encoding="utf-8")
        chunks = parse_markdown(str(md))
        assert chunks[0].source_id == "myfile.md"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_markdown("nonexistent.md")


class TestTextParser:

    def test_basic_parse(self, tmp_path):
        txt = tmp_path / "notes.txt"
        txt.write_text(
            "Line one\n"
            "Line two\n"
            "Line three\n",
            encoding="utf-8"
        )
        chunks = parse_text(str(txt))
        assert len(chunks) == 1
        assert chunks[0].source == "text"
        assert "Line one" in chunks[0].text

    def test_empty_file_returns_empty(self, tmp_path):
        txt = tmp_path / "empty.txt"
        txt.write_text("", encoding="utf-8")
        chunks = parse_text(str(txt))
        assert chunks == []

    def test_returns_chunk_object(self, tmp_path):
        txt = tmp_path / "test.txt"
        txt.write_text("Hello world", encoding="utf-8")
        chunks = parse_text(str(txt))
        assert isinstance(chunks[0], Chunk)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_text("nonexistent.txt")


class TestUrlParser:

    def test_invalid_url_returns_empty(self):
        from parsers.url import parse_url
        chunks = parse_url("http://localhost:99999/invalid")
        assert chunks == []

    def test_never_raises(self):
        from parsers.url import parse_url
        try:
            chunks = parse_url("not-a-url-at-all")
            assert isinstance(chunks, list)
        except Exception as e:
            pytest.fail(f"parse_url raised an exception: {e}")