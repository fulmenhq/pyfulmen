"""Tests for the W2B verify/multi-hash/reader API surface.

Covers verify_bytes/verify_text/verify_file/verify_reader,
multi_hash_bytes/_text/_file/_reader, hash_reader, the reader contract
(non-seekable support, text-mode rejection), chunk_size validation, and
the verify()/multi_hash() str-branch deprecation warnings.
"""

import io

import pytest

from pyfulmen.fulhash import (
    DEFAULT_CHUNK_SIZE,
    Algorithm,
    InvalidChecksumFormatError,
    UnsupportedAlgorithmError,
    hash_bytes,
    hash_file,
    hash_reader,
    hash_string,
    multi_hash,
    multi_hash_bytes,
    multi_hash_file,
    multi_hash_reader,
    multi_hash_text,
    verify,
    verify_bytes,
    verify_file,
    verify_reader,
    verify_text,
)

DATA = b"123456789"
DATA_XXH3 = hash_bytes(DATA).formatted
DATA_SHA256 = hash_bytes(DATA, Algorithm.SHA256).formatted
DATA_CRC32 = "crc32:cbf43926"


class NonSeekableReader:
    """Binary reader that denies seek/tell — models pipes/sockets/stdin.buffer."""

    def __init__(self, data: bytes) -> None:
        self._inner = io.BytesIO(data)

    def read(self, size: int = -1) -> bytes:
        return self._inner.read(size)

    def seekable(self) -> bool:
        return False

    def seek(self, *args: object, **kwargs: object) -> int:
        raise OSError("seek not supported")

    def tell(self) -> int:
        raise OSError("tell not supported")


class TestVerifyBytes:
    """Test verify_bytes()."""

    def test_match(self):
        assert verify_bytes(DATA, DATA_XXH3) is True
        assert verify_bytes(DATA, DATA_SHA256) is True
        assert verify_bytes(DATA, DATA_CRC32) is True

    def test_mismatch(self):
        assert verify_bytes(b"wrong", DATA_XXH3) is False
        assert verify_bytes(b"wrong", DATA_CRC32) is False

    def test_invalid_checksum_format(self):
        with pytest.raises(InvalidChecksumFormatError):
            verify_bytes(DATA, "no-separator")

    def test_unsupported_algorithm(self):
        with pytest.raises(UnsupportedAlgorithmError):
            verify_bytes(DATA, "md5:abc123def456")


class TestVerifyText:
    """Test verify_text()."""

    def test_match(self):
        expected = hash_string("Hello, World!").formatted
        assert verify_text("Hello, World!", expected) is True

    def test_mismatch(self):
        expected = hash_string("Hello, World!").formatted
        assert verify_text("different", expected) is False

    def test_encoding(self):
        expected = hash_string("héllo", encoding="latin-1").formatted
        assert verify_text("héllo", expected, encoding="latin-1") is True
        # UTF-8 encoding of the same text differs
        assert verify_text("héllo", expected) is False

    def test_never_treated_as_path(self, tmp_path):
        """A str naming an existing file is hashed as text, not read."""
        f = tmp_path / "data.txt"
        f.write_bytes(DATA)
        text_expected = hash_string(str(f)).formatted
        assert verify_text(str(f), text_expected) is True
        # And the file-content digest does NOT match the text digest
        assert verify_text(str(f), hash_file(f).formatted) is False

    def test_invalid_checksum_format(self):
        with pytest.raises(InvalidChecksumFormatError):
            verify_text("data", "bad")


class TestVerifyFile:
    """Test verify_file()."""

    def test_match(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(DATA)
        assert verify_file(f, DATA_XXH3) is True
        assert verify_file(str(f), DATA_SHA256) is True

    def test_mismatch(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"other content")
        assert verify_file(f, DATA_XXH3) is False

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="File not found"):
            verify_file(tmp_path / "missing.bin", DATA_XXH3)

    def test_directory(self, tmp_path):
        with pytest.raises(IsADirectoryError):
            verify_file(tmp_path, DATA_XXH3)

    def test_custom_chunk_size(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(DATA)
        assert verify_file(f, DATA_XXH3, chunk_size=3) is True

    def test_invalid_chunk_size(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(DATA)
        with pytest.raises(ValueError, match="chunk_size"):
            verify_file(f, DATA_XXH3, chunk_size=0)

    @pytest.mark.parametrize(
        "bad_chunk_size",
        [True, False, 3.5, "64", 1 << 100],
        ids=["bool-true", "bool-false", "float", "str", "huge-int"],
    )
    def test_chunk_size_rejects_non_positive_ints(self, tmp_path, bad_chunk_size):
        """Non-int, bool, and beyond-ssize_t values fail validation, not read()."""
        f = tmp_path / "data.bin"
        f.write_bytes(DATA)
        with pytest.raises(ValueError, match="chunk_size"):
            verify_file(f, DATA_XXH3, chunk_size=bad_chunk_size)

    def test_invalid_checksum_format(self, tmp_path):
        with pytest.raises(InvalidChecksumFormatError):
            verify_file(tmp_path / "data.bin", "bad")


class TestVerifyReader:
    """Test verify_reader()."""

    def test_match(self):
        assert verify_reader(io.BytesIO(DATA), DATA_XXH3) is True

    def test_mismatch(self):
        assert verify_reader(io.BytesIO(b"wrong"), DATA_XXH3) is False

    def test_non_seekable(self):
        assert verify_reader(NonSeekableReader(DATA), DATA_SHA256) is True

    def test_reads_from_current_position(self):
        buf = io.BytesIO(b"skip-" + DATA)
        buf.read(5)  # advance past prefix
        assert verify_reader(buf, DATA_XXH3) is True

    def test_text_mode_rejected(self):
        with pytest.raises(TypeError, match="binary stream"):
            verify_reader(io.StringIO("123456789"), DATA_XXH3)

    def test_invalid_chunk_size(self):
        with pytest.raises(ValueError, match="chunk_size"):
            verify_reader(io.BytesIO(DATA), DATA_XXH3, chunk_size=-1)


class TestHashReader:
    """Test hash_reader()."""

    def test_matches_block_hash(self):
        assert hash_reader(io.BytesIO(DATA)).hex == hash_bytes(DATA).hex

    def test_algorithms(self):
        for algo in [Algorithm.XXH3_128, Algorithm.SHA256, Algorithm.CRC32, Algorithm.CRC32C]:
            assert hash_reader(io.BytesIO(DATA), algo).hex == hash_bytes(DATA, algo).hex

    def test_empty_stream(self):
        assert hash_reader(io.BytesIO(b"")).hex == hash_bytes(b"").hex

    def test_non_seekable(self):
        digest = hash_reader(NonSeekableReader(DATA))
        assert digest.hex == hash_bytes(DATA).hex

    def test_reads_from_current_position_never_seeks(self):
        buf = io.BytesIO(b"prefix" + DATA)
        buf.read(6)
        assert hash_reader(buf).hex == hash_bytes(DATA).hex

    def test_stream_not_closed_position_at_eof(self):
        buf = io.BytesIO(DATA)
        hash_reader(buf)
        assert not buf.closed
        assert buf.tell() == len(DATA)

    def test_chunk_size_respected(self):
        digest = hash_reader(io.BytesIO(DATA), chunk_size=2)
        assert digest.hex == hash_bytes(DATA).hex

    def test_default_chunk_size_constant(self):
        assert DEFAULT_CHUNK_SIZE == 64 * 1024

    def test_text_mode_rejected(self):
        with pytest.raises(TypeError, match="binary stream"):
            hash_reader(io.StringIO("data"))

    def test_text_mode_open_rejected(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("data")
        with open(f) as reader, pytest.raises(TypeError, match="binary stream"):  # text mode
            hash_reader(reader)  # type: ignore[arg-type]

    def test_invalid_chunk_size(self):
        with pytest.raises(ValueError, match="chunk_size"):
            hash_reader(io.BytesIO(DATA), chunk_size=0)


class TestMultiHashVariants:
    """Test multi_hash_bytes/_text/_file/_reader."""

    ALGOS = [Algorithm.XXH3_128, Algorithm.SHA256, Algorithm.CRC32]

    def test_multi_hash_bytes(self):
        digests = multi_hash_bytes(DATA, self.ALGOS)
        assert len(digests) == 3
        for algo in self.ALGOS:
            assert digests[algo].hex == hash_bytes(DATA, algo).hex

    def test_multi_hash_bytes_empty_algorithms(self):
        assert multi_hash_bytes(DATA, []) == {}

    def test_multi_hash_text(self):
        digests = multi_hash_text("123456789", self.ALGOS)
        for algo in self.ALGOS:
            assert digests[algo].hex == hash_bytes(DATA, algo).hex

    def test_multi_hash_text_encoding(self):
        digests = multi_hash_text("héllo", [Algorithm.XXH3_128], encoding="latin-1")
        expected = hash_bytes("héllo".encode("latin-1"))
        assert digests[Algorithm.XXH3_128].hex == expected.hex

    def test_multi_hash_file(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(DATA)
        digests = multi_hash_file(f, self.ALGOS, chunk_size=4)
        for algo in self.ALGOS:
            assert digests[algo].hex == hash_bytes(DATA, algo).hex

    def test_multi_hash_file_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            multi_hash_file(tmp_path / "missing.bin", self.ALGOS)

    def test_multi_hash_file_invalid_chunk_size(self, tmp_path):
        with pytest.raises(ValueError, match="chunk_size"):
            multi_hash_file(tmp_path / "data.bin", self.ALGOS, chunk_size=0)

    def test_multi_hash_reader(self):
        digests = multi_hash_reader(io.BytesIO(DATA), self.ALGOS, chunk_size=2)
        for algo in self.ALGOS:
            assert digests[algo].hex == hash_bytes(DATA, algo).hex

    def test_multi_hash_reader_non_seekable(self):
        digests = multi_hash_reader(NonSeekableReader(DATA), self.ALGOS)
        for algo in self.ALGOS:
            assert digests[algo].hex == hash_bytes(DATA, algo).hex

    def test_multi_hash_reader_text_mode_rejected(self):
        with pytest.raises(TypeError, match="binary stream"):
            multi_hash_reader(io.StringIO("data"), self.ALGOS)

    def test_multi_hash_reader_invalid_chunk_size(self):
        with pytest.raises(ValueError, match="chunk_size"):
            multi_hash_reader(io.BytesIO(DATA), self.ALGOS, chunk_size=-5)


class TestDispatcherDeprecation:
    """Test verify()/multi_hash() dispatchers and str-branch deprecation."""

    def test_verify_bytes_branch_no_warning(self, recwarn):
        assert verify(DATA, DATA_XXH3) is True
        assert not [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]

    def test_verify_path_branch_no_warning(self, tmp_path, recwarn):
        f = tmp_path / "data.bin"
        f.write_bytes(DATA)
        assert verify(f, DATA_XXH3) is True
        assert not [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]

    def test_verify_str_branch_warns(self):
        with pytest.warns(DeprecationWarning, match="Passing a str to fulhash.verify"):
            assert verify("123456789", DATA_XXH3) is True

    def test_verify_str_warning_names_replacements(self):
        with pytest.warns(DeprecationWarning) as record:
            verify("123456789", DATA_XXH3)
        message = str(record[0].message)
        assert "verify_text()" in message
        assert "verify_bytes()" in message
        assert "verify_file()" in message
        assert "removed in v0.5.0" in message

    def test_verify_unsupported_type(self):
        with pytest.raises(TypeError, match="Unsupported source type"):
            verify(12345, DATA_XXH3)  # type: ignore[arg-type]

    def test_multi_hash_bytes_branch_no_warning(self, recwarn):
        digests = multi_hash(DATA, [Algorithm.CRC32])
        assert digests[Algorithm.CRC32].hex == "cbf43926"
        assert not [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]

    def test_multi_hash_path_branch_no_warning(self, tmp_path, recwarn):
        f = tmp_path / "data.bin"
        f.write_bytes(DATA)
        digests = multi_hash(f, [Algorithm.CRC32])
        assert digests[Algorithm.CRC32].hex == "cbf43926"
        assert not [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]

    def test_multi_hash_str_branch_warns(self):
        with pytest.warns(DeprecationWarning, match="Passing a str to fulhash.multi_hash"):
            digests = multi_hash("123456789", [Algorithm.CRC32])
        assert digests[Algorithm.CRC32].hex == "cbf43926"

    def test_multi_hash_str_warning_names_replacements(self):
        with pytest.warns(DeprecationWarning) as record:
            multi_hash("123456789", [Algorithm.CRC32])
        message = str(record[0].message)
        assert "multi_hash_text()" in message
        assert "multi_hash_bytes()" in message
        assert "multi_hash_file()" in message
        assert "removed in v0.5.0" in message

    def test_multi_hash_unsupported_type(self):
        with pytest.raises(TypeError, match="Unsupported source type"):
            multi_hash(12345, [Algorithm.CRC32])  # type: ignore[arg-type]

    def test_verify_file_delegates_to_hash_file_error_wording(self, tmp_path):
        """Path branch error wording preserved after hash_file delegation."""
        missing = tmp_path / "missing.bin"
        with pytest.raises(FileNotFoundError, match=f"File not found: {missing}"):
            verify(missing, DATA_XXH3)
